#     Dodo - A graphical, hackable email client based on notmuch
#     Copyright (C) 2021 - Aleks Kissinger
#
# This file is part of Dodo
#
# Dodo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dodo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Dodo. If not, see <https://www.gnu.org/licenses/>.

import email
import re
from io import BytesIO
from . import settings
from . import util

# gnupg is only needed for pgp/mime support, do not throw when not present
try:
    import gnupg
except ImportError as ex:
    pass

Gpg = gnupg.GPG(gnupghome=settings.gnupg_home, use_agent=True)

def copy_message(msg):
    gpg_policy = msg.policy.clone(linesep='\r\n',utf8=True)
    text_to_sign = BytesIO()
    gen = email.generator.BytesGenerator(text_to_sign,policy=gpg_policy)
    gen.flatten(msg)
    text_to_sign.seek(0)
    copy = email.message_from_binary_file(text_to_sign,policy=gpg_policy)
    text_to_sign.close()  # Discard the buffer
    return copy

# This functions alters the message passed as argument!
def move_headers_to_container(msg):
    container = email.message.EmailMessage(policy=msg.policy.clone())
    for k, v in msg.items():
        if not k.lower().startswith('content-'):
            container[k] = v
            del msg[k]
    return container

def sign(msg: email.message.EmailMessage) -> email.message.EmailMessage:
    RFC4880_HASH_ALGO = {'1': "MD5", '2': "SHA1", '3': "RIPEMD160",
                         '8': "SHA256", '9': "SHA384", '10': "SHA512",
                         '11': "SHA224"}

    # Generate a copy of the message with <CR><LF> line separators as
    # required .per rfc-3156
    # Moreover, by working on the copy we leave the original message
    # (msg) unaltered.
    msg_to_sign = copy_message(msg)

    # Create a new message that will contain the original message and the
    # pgp-signature. Move the non Content-* headers to the new message
    signed_mail = move_headers_to_container(msg_to_sign)
    signed_mail.set_type("multipart/signed")
    signed_mail.set_param("protocol", "application/pgp-signature")

    # Attach the message to be signed
    signed_mail.attach(msg_to_sign)

    # Create the signature based on attached message
    sig = Gpg.sign(str(signed_mail.get_payload(0)), keyid=settings.gnupg_keyid, detach=True)

    # Attach the signature to the new message
    sigpart = email.message.EmailMessage()
    sigpart['Content-Type'] = 'application/pgp-signature'
    sigpart.set_payload(str(sig))
    signed_mail.attach(sigpart)
    signed_mail.set_param("micalg", 'pgp-' +
                          RFC4880_HASH_ALGO[sig.hash_algo].lower())
    return signed_mail

def encrypt(msg: email.message.EmailMessage) -> email.message.EmailMessage:
    # Always also encrypt with the key corresponding to the From address in order to
    # be able to decrypt the mail that has been sent.
    email_sep = re.compile('\s*,\s*')
    recipients = [ addr for key,val in msg.items() if key in ['To', 'From', 'Cc']
                               for addr in email_sep.split(val) ]
    recipients_keys = [ x['fingerprint'] for x in Gpg.list_keys()
                       if any( re.search(util.strip_email_address(addr), y)
                              for y in x['uids']
                              for addr in recipients) ]
    # Generate a copy of the message, by working on the copy we leave
    #the original message (msg) unaltered.
    msg_to_encrypt = copy_message(msg)

    # Create a new message that will contain the control part and the encrypted
    # message.  *Move* the non Content-* headers to the new message
    encrypted_mail = move_headers_to_container(msg_to_encrypt)
    encrypted_mail.set_type("multipart/encrypted")
    encrypted_mail.set_param("protocol", "application/pgp-encrypted")

    # Create and add control part
    control_part = email.message.EmailMessage()
    control_part.set_content(b'Version:1', 'application', 'pgp-encrypted',
                             disposition='PGP/MIME version information',cte='7bit')
    encrypted_mail.attach(control_part)

    # Encrypt the parts of the original message (with non-content headers removed)
    encrypted_contents = str(Gpg.encrypt(msg_to_encrypt.as_string(), recipients_keys,
                          extra_args=['--emit-version']))

    # Attach the encrypted parts to the new message
    pgp_encrypted_part = email.message.EmailMessage()
    pgp_encrypted_part.set_content(encrypted_contents.encode(),'application',
                                   'octet-stream', disposition='inline', cte='7bit')
    encrypted_mail.attach(pgp_encrypted_part)
    return encrypted_mail


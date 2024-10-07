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
import email.utils
from . import settings
from . import util

# gnupg is only needed for pgp/mime support, do not throw when not present
try:
    import gnupg
    Gpg = gnupg.GPG(gnupghome=settings.gnupg_home, use_agent=True)
except (ImportError, NameError):
    Gpg = None


def ensure_gpg():
    if Gpg is None:
        raise Exception("python-gnupg is needed to sign/encrypt")


def sign(msg: email.message.EmailMessage) -> email.message.EmailMessage:
    ensure_gpg()
    RFC4880_HASH_ALGO = {'1': "MD5", '2': "SHA1", '3': "RIPEMD160",
                         '8': "SHA256", '9': "SHA384", '10': "SHA512",
                         '11': "SHA224"}

    # Generate a 7-bit clean copy of the message with <CR><LF> line separators as
    # required per rfc-3156
    # Moreover, by working on the copy we leave the original message
    # (msg) unaltered.
    gpg_policy = msg.policy.clone(linesep='\r\n', utf8=False)
    msg_to_sign = email.message_from_string(msg.as_string(), policy=gpg_policy)
    # Create a new mail that will contain the original message and its signature
    signed_mail = email.message.EmailMessage(policy=msg.policy.clone(linesep='\r\n'))
    # copy the non Content-* headers to the new mail and remove them form the
    # message that will be signed
    for k, v in msg.items():
        if not k.lower().startswith('content-'):
            signed_mail[k] = v
            del msg_to_sign[k]
    signed_mail.set_type("multipart/signed")
    signed_mail.set_param("protocol", "application/pgp-signature")

    # Attach the message to be signed
    signed_mail.attach(msg_to_sign)
    # Create the signature
    sig = Gpg.sign(msg_to_sign.as_string(), keyid=settings.gnupg_keyid, detach=True)
    # Attach the ASCII representation (as per rfc) of the signature, note that
    # set_content with contaent-type other then text requires a bytes object
    sigpart = email.message.EmailMessage()
    sigpart.set_content(str(sig).encode(), 'application', 'pgp-signature',
                        filename='signature.asc', cte='7bit')
    signed_mail.attach(sigpart)
    signed_mail.set_param("micalg", 'pgp-' + RFC4880_HASH_ALGO[sig.hash_algo].lower())
    return signed_mail


def encrypt(msg: email.message.EmailMessage) -> email.message.EmailMessage:
    ensure_gpg()
    # Always also encrypt with the key corresponding to the From address in order to
    # be able to decrypt the mail that has been sent.
    recipients = [
        addr[1] for addr in email.utils.getaddresses([
            val for key, val in msg.items() if key in ['From', 'To', 'Cc']
        ])
    ]
    recipients_keys = [key['fingerprint'] for key in Gpg.list_keys()
                       if any(addr == util.strip_email_address(uid)
                           for uid in key['uids'] for addr in recipients)]
    # Generate a copy of the message, by working on the copy we leave
    # the original message (msg) unaltered.
    msg_to_encrypt = email.message_from_bytes(msg.as_bytes(), policy=msg.policy.clone())
    # Create a new message that will contain the control part and the encrypted
    # message. Copy the non Content-* headers and remove them form the
    # message that will be encrypted
    encrypted_mail = email.message.EmailMessage(policy=msg.policy.clone())
    for k, v in msg.items():
        if not k.lower().startswith('content-'):
            encrypted_mail[k] = v
            del msg_to_encrypt[k]
    encrypted_mail.set_type("multipart/encrypted")
    encrypted_mail.set_param("protocol", "application/pgp-encrypted")

    # Create and add control part
    control_part = email.message.EmailMessage()
    control_part.set_content(b'Version:1', 'application', 'pgp-encrypted',
                             disposition='PGP/MIME version information', cte='7bit')
    encrypted_mail.attach(control_part)

    # Encrypt the parts of the original message (with non-content headers removed)
    encrypted_contents = Gpg.encrypt(msg_to_encrypt.as_bytes(), recipients_keys,
                                     extra_args=['--emit-version'])

    # attach the ASCII representation of the encrypted test, note that
    # set_content with contaent-type other then text requires a bytes object
    pgp_encrypted_part = email.message.EmailMessage()
    pgp_encrypted_part.set_content(str(encrypted_contents).encode(), 'application',
                                   'octet-stream', disposition='inline',
                                   filename='encrypred.asc', cte='7bit')
    encrypted_mail.attach(pgp_encrypted_part)
    return encrypted_mail

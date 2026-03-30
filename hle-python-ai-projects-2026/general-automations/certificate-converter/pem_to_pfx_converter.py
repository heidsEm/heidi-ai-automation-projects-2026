from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12


def parse_pem_file(pem_path):
   with open(pem_path, "rb") as f:
       pem_data = f.read()

   private_key = None
   certificates = []

   # Load private key (if present)
   try:
       private_key = serialization.load_pem_private_key(
           pem_data,
           password=None,
       )
   except ValueError:
       pass  # No private key found in file

   # Extract certificates
   for cert in pem_data.split(b"-----END CERTIFICATE-----"):
       if b"-----BEGIN CERTIFICATE-----" in cert:
           cert_block = cert + b"-----END CERTIFICATE-----\n"
           certificates.append(
               x509.load_pem_x509_certificate(cert_block)
           )

   if not certificates:
       raise ValueError("No certificates found in PEM file")

   # First certificate = leaf cert
   certificate = certificates[0]
   additional_certs = certificates[1:] if len(certificates) > 1 else []

   return private_key, certificate, additional_certs


def convert_single_pem_to_pfx(pem_path, output_pfx, password):
   key, cert, chain = parse_pem_file(pem_path)

   if key is None:
       raise ValueError("Private key not found in PEM file")

   pfx = pkcs12.serialize_key_and_certificates(
       name=b"my-cert",
       key=key,
       cert=cert,
       cas=chain,
       encryption_algorithm=serialization.BestAvailableEncryption(
           password.encode()
       ),
   )

   with open(output_pfx, "wb") as f:
       f.write(pfx)

   print(f"PFX written to: {output_pfx}")


# Usage
convert_single_pem_to_pfx(
   "Sectigo.pem",
   "Sectigo.pfx",
   "2026PFX",
)
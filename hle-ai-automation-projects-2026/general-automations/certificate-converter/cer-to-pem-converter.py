from cryptography import x509
from cryptography.hazmat.primitives import serialization


def convert_cer_to_pem(cer_path, pem_path):
    with open(cer_path, 'rb') as cer_file:
        cer_data = cer_file.read()

    # Load the certificate from the .cer file
    cert = x509.load_der_x509_certificate(cer_data)

    # Write the certificate to a .pem file
    with open(pem_path, 'wb') as pem_file:
        pem_data = cert.public_bytes(encoding=serialization.Encoding.PEM)
        pem_file.write(pem_data)

    print(f"Certificate has been converted to PEM format: {pem_path}")

# Usage Example
convert_cer_to_pem("Sectigo.cer", "Sectigo.pem")

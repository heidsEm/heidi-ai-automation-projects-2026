from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, pkcs12


def convert_pfx_to_cer(pfx_path, pfx_password, cer_output_path):
    # Read the .pfx file
    with open(pfx_path, 'rb') as pfx_file:
        pfx_data = pfx_file.read()

    # Load PFX contents
    private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
        data=pfx_data,
        password=pfx_password.encode(),
        backend=default_backend()
    )

    # Export the certificate to .cer file in PEM format
    if certificate:
        with open(cer_output_path, 'wb') as cer_file:
            cer_file.write(certificate.public_bytes(Encoding.PEM))
        print(f".cer file written to {cer_output_path}")
    else:
        print("No certificate found in PFX file.")

# Example usage
convert_pfx_to_cer("Sectigo.pfx", "CertCCIS-PFX51205", "Sectigo.cer")

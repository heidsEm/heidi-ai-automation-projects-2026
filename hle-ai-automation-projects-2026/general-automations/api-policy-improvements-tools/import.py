import base64
 
with open('Picture1.png', 'rb') as binary_file:
    binary_file_data = binary_file.read()
    base64_encoded_data = base64.b64encode(binary_file_data)
    base64_output = base64_encoded_data.decode('utf-8')
 
    print(base64_output)
 
import qrcode

# Link you want to convert
data = input("Enter link: ")

# Create QR
qr = qrcode.make(data)

# Save image
filename = "qr_code.png"
qr.save(filename)

print(f"QR code saved as {filename}")
import africastalking

africastalking.initialize("USERNAME", "API_KEY")
sms = africastalking.SMS

def send_sms(phone, message):
    sms.send(message, [phone])

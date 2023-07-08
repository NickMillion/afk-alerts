CUSTOM_ALERTS = {
    "This is an example alert": "This is an example alert",
}

def customValidCheck(chatText, alert):
    if alert.lower() in chatText.lower():
        return True
    else:
        return False
import re

file_path = r'c:\Users\money\HustleProjects\investment\core\templates\core\profile.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken template tags
content = re.sub(r'\{% if\s+user\.two_factor_enabled %\}', '{% if user.two_factor_enabled %}', content)
content = re.sub(r'id="email_notifications"\s+name="email_notifications"', 'id="email_notifications" name="email_notifications"', content)  
content = re.sub(r'id="sms_notifications"\s+name="sms_notifications"', 'id="sms_notifications" name="sms_notifications"', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
    
print('Fixed template')

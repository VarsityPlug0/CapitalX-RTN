import ast
import sys

def check_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content)
        print(f"✅ Syntax OK: {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax Error in {file_path}")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Message: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

if __name__ == "__main__":
    file_path = r"c:\Users\money\HustleProjects\BevanTheDev\capital x update\core\views.py"
    check_syntax(file_path)

@login_required
def user_financial_info_api(request):
    """
    API endpoint that returns user's financial information:
    - Wallet balance
    - Active investments
    - Recent deposits
    - Recent withdrawals
    - Investment plans
    """
    pass

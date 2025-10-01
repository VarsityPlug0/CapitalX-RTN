from django.core.management.base import BaseCommand
from core.models import Deposit

class Command(BaseCommand):
    help = 'Check details of a deposit by ID'

    def add_arguments(self, parser):
        parser.add_argument('deposit_id', type=int, help='ID of the deposit to check')

    def handle(self, *args, **options):
        deposit_id = options['deposit_id']
        
        try:
            # Get the deposit
            deposit = Deposit.objects.get(id=deposit_id)
            
            self.stdout.write(f'Deposit ID: {deposit.id}')
            self.stdout.write(f'User: {deposit.user.username} ({deposit.user.email})')
            self.stdout.write(f'Amount: R{deposit.amount}')
            self.stdout.write(f'Payment Method: {deposit.get_payment_method_display()}')
            self.stdout.write(f'Status: {deposit.get_status_display()}')
            self.stdout.write(f'Created: {deposit.created_at}')
            self.stdout.write(f'Updated: {deposit.updated_at}')
            
            # Payment method specific details
            if deposit.payment_method == 'card':
                self.stdout.write(f'Cardholder Name: {deposit.cardholder_name or "N/A"}')
                self.stdout.write(f'Card Last 4: {deposit.card_last4 or "N/A"}')
            elif deposit.payment_method == 'bitcoin':
                self.stdout.write(f'Bitcoin Address: {deposit.bitcoin_address or "N/A"}')
                self.stdout.write(f'Bitcoin Amount: {deposit.bitcoin_amount or "N/A"}')
                self.stdout.write(f'Bitcoin TXID: {deposit.bitcoin_txid or "N/A"}')
            elif deposit.payment_method == 'voucher':
                self.stdout.write(f'Voucher Code: {deposit.voucher_code or "N/A"}')
                self.stdout.write(f'Voucher Image: {"Yes" if deposit.voucher_image else "No"}')
                if deposit.voucher_image:
                    self.stdout.write(f'Voucher Image URL: {deposit.voucher_image.url if hasattr(deposit.voucher_image, "url") else "N/A"}')
            else:
                # EFT, cash, etc.
                self.stdout.write(f'Proof Image: {"Yes" if deposit.proof_image else "No"}')
                if deposit.proof_image:
                    self.stdout.write(f'Proof Image URL: {deposit.proof_image.url if hasattr(deposit.proof_image, "url") else "N/A"}')
            
            self.stdout.write(f'Admin Notes: {deposit.admin_notes or "N/A"}')
            
        except Deposit.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Deposit {deposit_id} not found.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking deposit: {str(e)}')
            )
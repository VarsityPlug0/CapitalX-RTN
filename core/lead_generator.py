"""
Automated Lead Generator for CapitalX Platform
============================================

This module provides automated lead generation with realistic names,
domains, and complete processing automation.

Author: CapitalX Development Team
Version: 1.0
"""

import random
from typing import List, Dict, Tuple
from django.utils import timezone
from .models import LeadCampaign, Lead
from .lead_system import EmailLeadSystem


class AutomatedLeadGenerator:
    """
    Automated lead generator that creates realistic leads
    and processes them automatically.
    """
    
    def __init__(self):
        self.first_names = [
            # Popular South African names
            "Thabo", "Nomsa", "Sipho", "Thandiwe", "Mandla", "Precious", "Bongani", "Nomfundo",
            "Kagiso", "Refilwe", "Tshepo", "Lerato", "Neo", "Katlego", "Tumelo", "Boitumelo",
            "Kefilwe", "Mmabatho", "Palesa", "Tebogo", "Karabo", "Bontle", "Lesego", "Phenyo",
            
            # International names
            "John", "Sarah", "Michael", "Emma", "David", "Lisa", "James", "Jennifer",
            "Robert", "Jessica", "William", "Ashley", "Christopher", "Amanda", "Matthew", "Melissa",
            "Andrew", "Michelle", "Joshua", "Kimberly", "Daniel", "Amy", "Anthony", "Angela",
            "Mark", "Brenda", "Donald", "Katherine", "Steven", "Nicole", "Paul", "Christine",
            "Kenneth", "Samantha", "Joseph", "Rachel", "Timothy", "Carolyn", "Kevin", "Janet",
            "Scott", "Virginia", "Brian", "Maria", "Charles", "Heather", "Thomas", "Diane",
            "Jeffrey", "Julie", "Ryan", "Joyce", "Jacob", "Victoria", "Gary", "Kelly",
            "Nicholas", "Christina", "Eric", "Joan", "Jonathan", "Evelyn", "Stephen", "Lauren",
            "Larry", "Judith", "Justin", "Megan", "Brandon", "Andrea", "Benjamin", "Cheryl",
            "Zachary", "Hannah", "Gregory", "Jacqueline", "Patrick", "Martha", "Alexander", "Gloria",
            "Jack", "Teresa", "Dennis", "Sara", "Jerry", "Janice", "Tyler", "Marie",
            "Aaron", "Julia", "Henry", "Kathryn", "Douglas", "Frances", "Peter", "Grace",
            "Noah", "Rose", "Carl", "Anna", "Arthur", "Jean", "Sean", "Alice",
            "Wayne", "Beverly", "Eugene", "Denise", "Ralph", "Marilyn", "Louis", "Amber"
        ]
        
        self.last_names = [
            # South African surnames
            "Mthembu", "Nkomo", "Dlamini", "Mokwena", "Mahlangu", "Chauke", "Mokoena", "Ndlovu",
            "Molefe", "Mabena", "Sibiya", "Maseko", "Zulu", "Radebe", "Khumalo", "Makhanya",
            "Ngwenya", "Sithole", "Mthethwa", "Hadebe", "Mbeki", "Mazibuko", "Ngcobo", "Cele",
            "Dube", "Gumede", "Shange", "Mtshali", "Mdlalose", "Zondi", "Khoza", "Bhengu",
            
            # International surnames  
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
            "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
            "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
            "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
            "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
            "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
            "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
            "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
            "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers"
        ]
        
        self.domains = [
            # Popular email providers
            "gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "icloud.com",
            "live.com", "aol.com", "protonmail.com", "mail.com", "zoho.com",
            
            # South African domains
            "mweb.co.za", "webmail.co.za", "telkomsa.net", "vodamail.co.za",
            "iafrica.com", "global.co.za", "saix.net", "worldonline.co.za",
            
            # Corporate domains (for variety)
            "company.com", "business.co.za", "enterprise.com", "corporation.net",
            "group.com", "holdings.co.za", "ventures.com", "solutions.net",
            "consulting.com", "services.co.za", "trading.com", "investments.net",
            
            # Tech domains
            "techstart.com", "innovation.net", "digital.co.za", "online.com",
            "web.co.za", "tech.net", "startup.com", "software.co.za"
        ]
        
        # Weight domains by popularity (gmail, outlook more likely)
        self.domain_weights = {
            "gmail.com": 25, "outlook.com": 20, "yahoo.com": 15, "hotmail.com": 10,
            "icloud.com": 8, "live.com": 5, "mweb.co.za": 4, "webmail.co.za": 3,
            "aol.com": 2, "protonmail.com": 2, "telkomsa.net": 2, "vodamail.co.za": 2,
            "iafrica.com": 1, "global.co.za": 1
        }
        
    def generate_realistic_leads(self, count: int, campaign: LeadCampaign) -> List[Lead]:
        """
        Generate realistic leads with varied names and domains.
        
        Args:
            count (int): Number of leads to generate
            campaign (LeadCampaign): Campaign to add leads to
            
        Returns:
            List[Lead]: Generated lead objects
        """
        leads = []
        used_combinations = set()
        
        # Create weighted domain list
        weighted_domains = []
        for domain, weight in self.domain_weights.items():
            weighted_domains.extend([domain] * weight)
        
        # Add remaining domains with weight 1
        for domain in self.domains:
            if domain not in self.domain_weights:
                weighted_domains.append(domain)
        
        for i in range(count):
            attempts = 0
            while attempts < 50:  # Prevent infinite loop
                first_name = random.choice(self.first_names)
                last_name = random.choice(self.last_names)
                domain = random.choice(weighted_domains)
                
                # Create unique combination
                combination = (first_name.lower(), last_name.lower(), domain.lower())
                
                if combination not in used_combinations:
                    used_combinations.add(combination)
                    
                    # Check if lead already exists in campaign
                    if not Lead.objects.filter(
                        campaign=campaign,
                        first_name=first_name,
                        last_name=last_name,
                        domain=domain
                    ).exists():
                        lead = Lead.objects.create(
                            campaign=campaign,
                            first_name=first_name,
                            last_name=last_name,
                            domain=domain,
                            status='pending'
                        )
                        leads.append(lead)
                        break
                
                attempts += 1
        
        # Update campaign statistics
        campaign.total_leads = campaign.leads.count()
        campaign.save()
        
        return leads
    
    def create_and_process_campaign(self, campaign_name: str, lead_count: int, 
                                  created_by, description: str = "") -> Dict:
        """
        Create a campaign, generate leads, and process them automatically.
        
        Args:
            campaign_name (str): Name for the new campaign
            lead_count (int): Number of leads to generate
            created_by: User who created the campaign
            description (str): Campaign description
            
        Returns:
            Dict: Processing results and statistics
        """
        try:
            # Create campaign
            campaign = LeadCampaign.objects.create(
                name=campaign_name,
                description=description or f"Auto-generated campaign with {lead_count} leads",
                created_by=created_by,
                is_active=True
            )
            
            # Generate leads
            leads = self.generate_realistic_leads(lead_count, campaign)
            
            # Process leads using EmailLeadSystem
            lead_system = EmailLeadSystem()
            
            # Convert to processing format
            leads_data = []
            for lead in leads:
                leads_data.append({
                    'first_name': lead.first_name,
                    'last_name': lead.last_name,
                    'domain': lead.domain,
                    'lead_id': lead.id
                })
            
            # Process the leads
            results = lead_system.process_lead_batch(leads_data)
            
            # Update database with results
            successful_leads = 0
            total_emails_sent = 0
            
            for i, result in enumerate(results):
                try:
                    lead = leads[i]
                    
                    # Update lead with results
                    lead.generated_emails = result.get('generated_emails', [])
                    lead.valid_emails = result.get('valid_emails', [])
                    lead.emails_sent = result.get('emails_sent', [])
                    lead.documents_created = result.get('documents_created', [])
                    lead.success = result.get('success', False)
                    lead.error_message = result.get('error', '')
                    lead.status = 'completed' if result.get('success') else 'failed'
                    lead.processed_at = timezone.now()
                    lead.save()
                    
                    if result.get('success'):
                        successful_leads += 1
                        total_emails_sent += len(result.get('emails_sent', []))
                        
                except Exception as e:
                    if i < len(leads):
                        lead = leads[i]
                        lead.status = 'failed'
                        lead.error_message = str(e)
                        lead.save()
            
            # Update campaign statistics
            campaign.total_leads = len(leads)
            campaign.emails_sent = total_emails_sent
            campaign.success_rate = (successful_leads / len(leads) * 100) if leads else 0
            campaign.save()
            
            return {
                'success': True,
                'campaign': campaign,
                'leads_generated': len(leads),
                'leads_processed': len(results),
                'successful_leads': successful_leads,
                'emails_sent': total_emails_sent,
                'success_rate': campaign.success_rate,
                'message': f'Successfully created and processed {len(leads)} leads with {successful_leads} successful contacts.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create and process campaign: {str(e)}'
            }
    
    def get_generation_suggestions(self) -> Dict:
        """
        Get suggestions for lead generation based on available data.
        
        Returns:
            Dict: Suggestions and statistics
        """
        return {
            'available_first_names': len(self.first_names),
            'available_last_names': len(self.last_names),
            'available_domains': len(self.domains),
            'max_unique_combinations': len(self.first_names) * len(self.last_names) * len(self.domains),
            'recommended_batch_sizes': [10, 25, 50, 100, 250, 500],
            'popular_domains': list(self.domain_weights.keys())[:10],
            'domain_distribution': {
                'professional': ['gmail.com', 'outlook.com', 'yahoo.com'],
                'south_african': ['mweb.co.za', 'webmail.co.za', 'telkomsa.net'],
                'corporate': ['company.com', 'business.co.za', 'enterprise.com'],
                'tech': ['techstart.com', 'innovation.net', 'digital.co.za']
            }
        }


class LeadProgressTracker:
    """
    Track progress of lead generation and processing operations.
    """
    
    def __init__(self):
        self.progress_data = {}
    
    def start_operation(self, operation_id: str, total_steps: int) -> None:
        """Start tracking an operation."""
        self.progress_data[operation_id] = {
            'total_steps': total_steps,
            'current_step': 0,
            'status': 'running',
            'message': 'Starting operation...',
            'start_time': timezone.now(),
            'errors': []
        }
    
    def update_progress(self, operation_id: str, step: int, message: str = "") -> None:
        """Update operation progress."""
        if operation_id in self.progress_data:
            self.progress_data[operation_id]['current_step'] = step
            self.progress_data[operation_id]['message'] = message
            self.progress_data[operation_id]['progress_percent'] = (
                step / self.progress_data[operation_id]['total_steps'] * 100
            )
    
    def complete_operation(self, operation_id: str, success: bool = True, 
                          final_message: str = "") -> None:
        """Mark operation as complete."""
        if operation_id in self.progress_data:
            self.progress_data[operation_id]['status'] = 'completed' if success else 'failed'
            self.progress_data[operation_id]['message'] = final_message
            self.progress_data[operation_id]['end_time'] = timezone.now()
            self.progress_data[operation_id]['progress_percent'] = 100
    
    def get_progress(self, operation_id: str) -> Dict:
        """Get current progress of an operation."""
        return self.progress_data.get(operation_id, {
            'status': 'not_found',
            'message': 'Operation not found'
        })
    
    def cleanup_old_operations(self, hours: int = 24) -> None:
        """Clean up operations older than specified hours."""
        cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
        
        operations_to_remove = []
        for op_id, data in self.progress_data.items():
            if data.get('start_time', timezone.now()) < cutoff_time:
                operations_to_remove.append(op_id)
        
        for op_id in operations_to_remove:
            del self.progress_data[op_id]


# Global progress tracker instance
progress_tracker = LeadProgressTracker()

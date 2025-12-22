from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Max

from accounts.models import (
    Role,
    BusinessGroup,
    Company,
    Department,
    Team,
    User,
    UserRole,
)
from accounts.services import AuthService

from tickets.models import (
    Category,
    SubCategory,
    Ticket,
    TicketHistory,
    ClosureCode,
)

from datetime import timedelta
import uuid
import re


class Command(BaseCommand):
    help = "Seed development data for ITSM UI testing"

    def handle(self, *args, **options):
        self.stdout.write("=== ITSM DEV SEED START ===")

        # ----------------------------------------------------
        # ROLES
        # ----------------------------------------------------
        roles = [
            (1, "USER"),
            (2, "EMPLOYEE"),
            (3, "MANAGER"),
            (4, "ADMIN"),
        ]

        for role_id, role_name in roles:
            Role.objects.get_or_create(
                id=role_id,
                defaults={"name": role_name},
            )

        self.stdout.write(self.style.SUCCESS("Roles ready"))

        # ----------------------------------------------------
        # ORG STRUCTURE
        # ----------------------------------------------------
        bg, _ = BusinessGroup.objects.get_or_create(name="Blackbox Corp")

        company, _ = Company.objects.get_or_create(
            name="Blackbox Technologies",
            business_group=bg,
        )

        department, _ = Department.objects.get_or_create(
            name="IT Support",
            company=company,
        )

        team, _ = Team.objects.get_or_create(
            name="Helpdesk Team Alpha",
            department=department,
        )

        self.stdout.write(self.style.SUCCESS("Organization structure ready"))

        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------
        PASSWORD = "Password@123"
        hashed_password = AuthService.hash_password(PASSWORD)

        users_data = [
            ("user1@demo.local", "User One", "user1"),
            ("employee1@demo.local", "Employee One", "employee1"),
            ("manager1@demo.local", "Manager One", "manager1"),
            ("admin1@demo.local", "Admin One", "admin1"),
        ]

        users = {}

        for email, name, alias in users_data:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "alias": alias,
                    "password": hashed_password,
                    "is_active": True,
                    "last_login": timezone.now(),
                },
            )
            users[email] = user

        team.manager = users["manager1@demo.local"]
        team.save(update_fields=["manager"])

        self.stdout.write(self.style.SUCCESS("Users ready"))

        # ----------------------------------------------------
        # USER ROLES
        # ----------------------------------------------------
        role_map = {
            "user1@demo.local": "USER",
            "employee1@demo.local": "EMPLOYEE",
            "manager1@demo.local": "MANAGER",
            "admin1@demo.local": "ADMIN",
        }

        for email, role_name in role_map.items():
            UserRole.objects.get_or_create(
                user=users[email],
                role=Role.objects.get(name=role_name),
                defaults={
                    "department": department if role_name != "ADMIN" else None,
                    "team": team if role_name in ("EMPLOYEE", "MANAGER") else None,
                },
            )

        self.stdout.write(self.style.SUCCESS("User roles assigned"))

        # ----------------------------------------------------
        # CATEGORIES & SUBCATEGORIES
        # ----------------------------------------------------
        hardware, _ = Category.objects.get_or_create(name="Hardware")
        software, _ = Category.objects.get_or_create(name="Software")

        def ensure_subcategory(name, category):
            SubCategory.objects.get_or_create(
                name=name,
                category=category,
                department=department,
                defaults={"id": uuid.uuid4()},
            )

        ensure_subcategory("Laptop / Desktop", hardware)
        ensure_subcategory("Printer / Scanner", hardware)
        ensure_subcategory("Email / Outlook", software)
        ensure_subcategory("VPN / Network", software)

        self.stdout.write(self.style.SUCCESS("Categories ready"))

        # ----------------------------------------------------
        # CLOSURE CODES
        # ----------------------------------------------------
        for code in ["RESOLVED", "WORKAROUND", "USER_CANCELLED"]:
            ClosureCode.objects.get_or_create(
                code=code,
                defaults={"id": uuid.uuid4()},
            )

        closure_codes = {c.code: c for c in ClosureCode.objects.all()}
        self.stdout.write(self.style.SUCCESS("Closure codes ready"))

        # ----------------------------------------------------
        # TICKET NUMBER SEQUENCE
        # ----------------------------------------------------
        today_prefix = timezone.now().strftime("TKT-%Y%m%d")

        latest_ticket = (
            Ticket.objects
            .filter(ticket_number__startswith=today_prefix)
            .aggregate(max_num=Max("ticket_number"))
            .get("max_num")
        )

        if latest_ticket:
            match = re.search(r"(\d{5})$", latest_ticket)
            ticket_seq = int(match.group(1)) + 1 if match else 1
        else:
            ticket_seq = 1

        def generate_ticket_number():
            nonlocal ticket_seq
            num = f"{today_prefix}-{ticket_seq:05d}"
            ticket_seq += 1
            return num

        self.stdout.write(f"Ticket sequence starting at {ticket_seq}")

        # ----------------------------------------------------
        # TICKET CREATION
        # ----------------------------------------------------
        now = timezone.now()
        creator = users["user1@demo.local"]
        assignee = users["employee1@demo.local"]
        subcategories = list(SubCategory.objects.all())

        def create_ticket(
            title,
            status,
            days_ago,
            assigned=False,
            priority=2,
            is_closed=False,
            closure_code=None,
        ):
            if is_closed:
                status = "CLOSED"

            created_at = now - timedelta(days=days_ago)

            ticket = Ticket.objects.create(
                id=uuid.uuid4(),
                ticket_number=generate_ticket_number(),
                title=title,
                description=f"Auto-seeded ticket: {title}",
                category=hardware if "Hardware" in title else software,
                subcategory=subcategories[hash(title) % len(subcategories)],
                department=department,
                created_by=creator,
                assigned_to=assignee if assigned else None,
                assigned_at=created_at if assigned else None,
                priority=priority,
                status=status,
                is_closed=is_closed,
                closure_code=closure_code,
                closed_at=created_at if is_closed else None,
                version=1,
                created_at=created_at,
                updated_at=created_at,
            )

            TicketHistory.objects.create(
                id=uuid.uuid4(),
                ticket=ticket,
                old_status="NEW",
                new_status=status,
                note="Initial ticket creation",
                changed_by=creator,
                changed_at=created_at,
            )

        # ----------------------------------------------------
        # DATASET
        # ----------------------------------------------------
        for i in range(3):
            create_ticket(
                title=f"Hardware Issue {i+1}",
                status="NEW",
                days_ago=20 - i,
            )

        for i in range(4):
            create_ticket(
                title=f"Assigned Software Issue {i+1}",
                status="ASSIGNED",
                assigned=True,
                days_ago=15 - i,
            )

        for i in range(2):
            create_ticket(
                title=f"In Progress Hardware {i+1}",
                status="IN_PROGRESS",
                assigned=True,
                priority=1 if i == 0 else 2,
                days_ago=10 - i,
            )

        create_ticket(
            title="Waiting on User Response",
            status="WAITING",
            assigned=True,
            days_ago=6,
        )

        create_ticket(
            title="On Hold Vendor Dependency",
            status="ON_HOLD",
            assigned=True,
            days_ago=5,
        )

        for i in range(3):
            create_ticket(
                title=f"Resolved Issue {i+1}",
                status="CLOSED",
                assigned=True,
                is_closed=True,
                closure_code=closure_codes["RESOLVED"],
                days_ago=30 - i,
            )

        self.stdout.write(self.style.SUCCESS("Tickets seeded successfully"))
        self.stdout.write("=== ITSM DEV SEED COMPLETE ===")

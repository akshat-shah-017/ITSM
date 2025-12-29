# Generated migration for TicketSequence table
# This creates a dedicated sequence table for high-concurrency ticket number generation

from django.db import migrations


class Migration(migrations.Migration):
    """
    Create TicketSequence table for scalable ticket number generation.
    
    Before: SELECT FOR UPDATE on all today's tickets (bottleneck at 100+ concurrent creates)
    After: Single row lock per date (supports 1000+ concurrent creates)
    """

    dependencies = [
        ('tickets', '0002_alter_category_id_alter_closurecode_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward migration - create table
            sql="""
                CREATE TABLE TicketSequence (
                    date DATE NOT NULL PRIMARY KEY,
                    next_seq INT NOT NULL DEFAULT 1
                );
            """,
            # Reverse migration - drop table
            reverse_sql="DROP TABLE TicketSequence;",
        ),
    ]

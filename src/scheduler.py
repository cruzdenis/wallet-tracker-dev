from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from src.models.models import AppSettings
from src.services.octav_service import OctavService

scheduler = BackgroundScheduler()


def sync_wallets_job():
    """Job to sync all wallets"""
    print(f"[{datetime.now()}] Running scheduled wallet sync...")
    
    try:
        results = OctavService.sync_all_wallets()
        print(f"Sync completed: {results['success']} successful, {results['failed']} failed")
        if results['errors']:
            for error in results['errors']:
                print(f"  - {error}")
    except Exception as e:
        print(f"Error in sync job: {e}")


def get_sync_interval():
    """Get sync interval from settings (in hours), default 12 hours"""
    setting = AppSettings.query.filter_by(key='sync_interval_hours').first()
    if setting and setting.value:
        try:
            return int(setting.value)
        except ValueError:
            pass
    return 12  # Default 12 hours


def update_scheduler_job():
    """Update scheduler job with current interval setting"""
    interval_hours = get_sync_interval()
    
    # Remove existing job if any
    if scheduler.get_job('wallet_sync'):
        scheduler.remove_job('wallet_sync')
    
    # Add new job with updated interval
    scheduler.add_job(
        func=sync_wallets_job,
        trigger=IntervalTrigger(hours=interval_hours),
        id='wallet_sync',
        name='Sync all wallets',
        replace_existing=True
    )
    
    print(f"Scheduler updated: syncing every {interval_hours} hours")


def init_scheduler(app):
    """Initialize the scheduler with Flask app context"""
    
    def job_wrapper():
        """Wrapper to run job within Flask app context"""
        with app.app_context():
            sync_wallets_job()
    
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started")
    
    # Add initial job
    with app.app_context():
        interval_hours = get_sync_interval()
        scheduler.add_job(
            func=job_wrapper,
            trigger=IntervalTrigger(hours=interval_hours),
            id='wallet_sync',
            name='Sync all wallets',
            replace_existing=True
        )
        print(f"Wallet sync job scheduled: every {interval_hours} hours")
    
    return scheduler


def trigger_immediate_sync(app):
    """Trigger an immediate sync of all wallets"""
    with app.app_context():
        sync_wallets_job()


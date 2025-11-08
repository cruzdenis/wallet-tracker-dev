import requests
import json
from datetime import datetime
from src.models.models import db, Wallet, BalanceHistory, ProtocolBalance, TokenBalance, AppSettings


class OctavService:
    """Service for interacting with Octav.fi API"""
    
    BASE_URL = "https://api.octav.fi"
    
    @staticmethod
    def get_api_key():
        """Get API key from settings"""
        setting = AppSettings.query.filter_by(key='octav_api_key').first()
        return setting.value if setting else None
    
    @staticmethod
    def fetch_portfolio(addresses, wait_for_sync=True):
        """
        Fetch portfolio data from Octav.fi API
        
        Args:
            addresses: Comma-separated list of wallet addresses or single address
            wait_for_sync: If True, wait for fresh data
            
        Returns:
            dict: API response data or None if error
        """
        api_key = OctavService.get_api_key()
        if not api_key:
            raise ValueError("Octav API key not configured")
        
        # Ensure addresses is a string
        if isinstance(addresses, list):
            addresses = ','.join(addresses)
        
        url = f"{OctavService.BASE_URL}/v1/portfolio"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        params = {
            'addresses': addresses,
            'includeImages': 'false',
            'includeExplorerUrls': 'false',
            'waitForSync': 'true' if wait_for_sync else 'false'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching portfolio from Octav API: {e}")
            return None
    
    @staticmethod
    def save_balance_snapshot(wallet_id, portfolio_data):
        """
        Save balance snapshot to database
        
        Args:
            wallet_id: Wallet database ID
            portfolio_data: Single wallet portfolio data from API
            
        Returns:
            BalanceHistory: Created balance history record
        """
        if not portfolio_data:
            return None
        
        # Create balance history record
        balance_history = BalanceHistory(
            wallet_id=wallet_id,
            timestamp=datetime.utcnow(),
            networth=float(portfolio_data.get('networth', 0)),
            data_json=json.dumps(portfolio_data)
        )
        db.session.add(balance_history)
        db.session.flush()  # Get the ID
        
        # Extract and save protocol balances
        asset_by_protocols = portfolio_data.get('assetByProtocols', {})
        for protocol_key, protocol_data in asset_by_protocols.items():
            # Get total value for this protocol across all chains
            protocol_value = float(protocol_data.get('value', 0))
            
            # Save protocol balance
            protocol_balance = ProtocolBalance(
                balance_history_id=balance_history.id,
                protocol_name=protocol_data.get('name', protocol_key),
                protocol_key=protocol_key,
                value=protocol_value,
                chain=None  # Aggregated across chains
            )
            db.session.add(protocol_balance)
            
            # Extract tokens from each chain
            chains = protocol_data.get('chains', {})
            for chain_key, chain_data in chains.items():
                protocol_positions = chain_data.get('protocolPositions', {})
                
                for position_type, position_data in protocol_positions.items():
                    # Get assets from this position
                    assets = position_data.get('assets', [])
                    for asset in assets:
                        token_balance = TokenBalance(
                            balance_history_id=balance_history.id,
                            token_symbol=asset.get('symbol', ''),
                            token_name=asset.get('name', ''),
                            balance=str(asset.get('balance', '0')),
                            value=float(asset.get('value', 0)),
                            price=float(asset.get('price', 0)),
                            chain=chain_key,
                            protocol=protocol_key
                        )
                        db.session.add(token_balance)
                    
                    # Also check for reward assets in farming positions
                    reward_assets = position_data.get('rewardAssets', [])
                    for asset in reward_assets:
                        token_balance = TokenBalance(
                            balance_history_id=balance_history.id,
                            token_symbol=asset.get('symbol', ''),
                            token_name=asset.get('name', ''),
                            balance=str(asset.get('balance', '0')),
                            value=float(asset.get('value', 0)),
                            price=float(asset.get('price', 0)),
                            chain=chain_key,
                            protocol=f"{protocol_key}_rewards"
                        )
                        db.session.add(token_balance)
        
        db.session.commit()
        return balance_history
    
    @staticmethod
    def sync_wallet(wallet_id):
        """
        Sync a single wallet with Octav API
        
        Args:
            wallet_id: Wallet database ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        wallet = Wallet.query.get(wallet_id)
        if not wallet:
            return False
        
        try:
            # Fetch portfolio data
            portfolio_data = OctavService.fetch_portfolio(wallet.address)
            if not portfolio_data:
                return False
            
            # Handle both list and dict responses
            if isinstance(portfolio_data, list):
                if len(portfolio_data) == 0:
                    return False
                wallet_data = portfolio_data[0]
            elif isinstance(portfolio_data, dict):
                wallet_data = portfolio_data
            else:
                return False
            
            # Save snapshot
            OctavService.save_balance_snapshot(wallet_id, wallet_data)
            
            # Update wallet last_synced timestamp
            wallet.last_synced = datetime.utcnow()
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error in sync_wallet: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def sync_all_wallets():
        """
        Sync all wallets with Octav API
        
        Returns:
            dict: Summary of sync results
        """
        wallets = Wallet.query.all()
        results = {
            'total': len(wallets),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for wallet in wallets:
            try:
                if OctavService.sync_wallet(wallet.id):
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to sync wallet {wallet.address}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error syncing wallet {wallet.address}: {str(e)}")
        
        return results


import random 
import time 
from loguru import logger 
 
from web3 import Web3 
 
import settings 
from modules.helper import accounts, cheker_gwei, sleeping, PROXY_ACC, USE_PROXY, retries 
from random import shuffle 
from settings import RPC, SHUFFLE_WALLET, nfts, nfts_mint 
from modules.abi_and_contract import MINT_ABI, BOOST_ABI 
from modules.wallet import Wallet 
from modules.relay import Relay 
 
 
def main_deposit_to_blast(): 
    for account in accounts: 
        cheker_gwei() 
        chek_deposit_balance(account) 
 
 
def find_network(wallet): 
    available_networks = settings.CHAINS_FOR_WITHDRAW.copy() 
    while available_networks: 
        selected_network = random.choice(available_networks) 
        try: 
            balance = wallet.get_balance(chain_name=selected_network, human=True) 
 
            if balance < (settings.AMOUNT_FOR_WITHDRAW[1] + 0.0001): 
                available_networks.remove(selected_network) 
                continue 
 
            return selected_network 
        except Exception as e: 
            logger.error( 
                f"Ошибка при получении баланса для сети {selected_network} в кошельке {wallet.address}: {str(e)}") 
            available_networks.remove(selected_network) 
    return None 
 
 
def chek_deposit_balance(account): 
    amount = None 
    wallet = Wallet(account.key, None) 
    if settings.USE_CHECK_BALANCE: 
        if wallet.get_balance('blast') < Web3.to_wei(settings.MIN_BALANCE_BLAST, 'ether'): 
            logger.error(f'{account.address} баланс меньше {settings.MIN_BALANCE_BLAST}') 
            wallet = Wallet(account.key, None) 
            if settings.USE_ONLY_BALANCE_ON_WALLET: 
                chain = find_network(wallet) 
            else: 
                chain = find_network(wallet) 
                if chain is None and settings.USE_WITHDRAW_OKX: 
                    chain = random.choice(settings.CHAINS_FOR_WITHDRAW) 
                    amount,s,a = wallet.okx_withdraw(chain) 
 
            if chain is None: 
                logger.error('Не нашли баланс в выбранных сетях') 
                return 
 
            Relay(wallet, chain, 'blast', amount) 
            sleeping() 
        else: 
            logger.info(f'{account.address} баланс в норме и больше {settings.MIN_BALANCE_BLAST}') 
 
 
def main_blastr(number): 
    chain_w3 = Web3(Web3.HTTPProvider(RPC)) 
 
    print(f'Загружено {len(accounts)} кошельков') 
 
    if SHUFFLE_WALLET: 
        shuffle(accounts) 
 
    for account in accounts: 
        if USE_PROXY: 
            proxy_list = PROXY_ACC[account.address].split(':') 
            proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}' 
            chain_w3 = Web3( 
                Web3.HTTPProvider(RPC, request_kwargs={"proxies": {'https': proxy, 'http': proxy}})) 
 
        cheker_gwei() 
        chek_deposit_balance(account) 
 
        if number == 1:  # boost 
            contract_nft = random.choice(nfts) 
            boost(chain_w3, account, contract_nft) 
        elif number == 2:  # unboost boost 
            random_count_boost = random.randint(1, 2) 
            logger.info(f'[{account.address}] Count unboost boost : {random_count_boost}') 
            for i in range(random_count_boost): 
                contract_nft = find_nft(chain_w3, account) 
                if contract_nft is None: 
                    break 
                unboost(chain_w3, account, contract_nft) 
                sleeping() 
                contract_nft = random.choice(nfts) 
                boost(chain_w3, account, contract_nft) 
                sleeping() 
        elif number == 3:  # mint 
            contract_nft = random.choice(nfts_mint) 
            mint_nft(chain_w3, account, contract_nft) 
        else: 
            contract_nft = find_nft(chain_w3, account) 
            unboost(chain_w3, account, contract_nft) 
 
        sleeping(settings.PAUSE_ACC_MIN, settings.PAUSE_ACC_MAX) 
 
 
@retries(settings.POVTOR_TX) 
def find_nft(w3, account):

import hashlib
import json
import copy

from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from beaker import sandbox

# def createAccount():
#     # Create an account
#     private_key, address = account.generate_account()
#     print(f"address: {address}")
#     print(f"private key: {private_key}")
#     print(f"mnemonic: {mnemonic.from_private_key(private_key)}")

#     # Create a connection to algorand
#     algodToken = ''
#     algodServer = 'https://testnet-api.algonode.cloud'
#     algodPort = None
#     algod_client = algod.AlgodClient(algodToken, address)

#     # Get account info and print to verify if it works
#     account_info: Dict[str, Any] = algod_client.account_info(address)
#     # print(f"account info is {account_info}")


def mintNFT(algod_client, creator_address, creator_private_key, asset_name, asset_unit_name):
    # Get account balance of account
    account_info: Dict[str, Any] = algod_client.account_info(creator_address)
    print(f"Account balance: {account_info.get('amount')} microAlgos")

    # Get suggested params
    params = algod_client.suggested_params()
    
    # Make transaction
    unsigned_txn = transaction.AssetCreateTxn(
        sender=creator_address, 
        sp=params, 
        total=1, 
        decimals=0, 
        default_frozen=False,
        unit_name=asset_unit_name,
        asset_name=asset_name,
        url="ipfs:://QmbPkCn3ZWsFM2cBmNvSGasRTbY97MCxtkrtuFaxbzmqpx#arc3"
    )

    # sign the transaction
    signed_txn = unsigned_txn.sign(creator_private_key)

    # submit the transaction and get back a transaction id
    txid = algod_client.send_transaction(signed_txn)
    print("Successfully submitted transaction with txID: {}".format(txid))

    # wait for confirmation
    txn_result = transaction.wait_for_confirmation(algod_client, txid, 4)
    created_asset = txn_result["asset-index"]
    print(f"Asset ID Created is {created_asset}")

    return created_asset  #your confirmed transaction's asset id should be returned instead


def transferNFT(algod_client, creator_address, creator_private_key, receiver_address, receiver_private_key, asset_id):
    # Account of receiver - Done

    # Get suggested params
    params = algod_client.suggested_params()

    # Optin asset transaction
    optInTxn = transaction.AssetOptInTxn(
        receiver_address, 
        sp=params, 
        index = asset_id
    )
       
    newParams = copy.deepcopy(params)
    newParams.fee = 2 * params.min_fee
    newParams.flat_fee = True

    # Fund Transaction
    fundTxn = transaction.PaymentTxn(
        sender=creator_address, 
        sp= newParams, 
        receiver=receiver_address, 
        amt=200_000
    )

    newParams2 = copy.deepcopy(params)
    newParams2.fee = 0
    newParams2.flat_fee = True

    # Send Asset transaction
    assetTxn = transaction.AssetTransferTxn(
        sender=creator_address, 
        sp=newParams2, 
        receiver=receiver_address, 
        amt=1, 
        index=asset_id
    )

    # Group Transactions
    txns = [fundTxn, optInTxn, assetTxn]
    txnGroup = transaction.assign_group_id(txns=txns)
    signedTxns = [
        txns[0].sign(creator_private_key),
        txns[1].sign(receiver_private_key),
        txns[2].sign(creator_private_key)
    ]

    # Send transactions
    transactRes = algod_client.send_transactions(signedTxns)
    update_result = transaction.wait_for_confirmation(algod_client, transactRes, 4)
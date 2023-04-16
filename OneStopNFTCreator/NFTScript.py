import hashlib
import json
import copy

from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from beaker import sandbox



def mintNFT(algod_client, creator_address, creator_private_key, asset_name, asset_unit_name):
    account_info: Dict[str, Any] = algod_client.account_info(creator_address)

    sugParams = algod_client.suggested_params()
    
    txn = transaction.AssetCreateTxn(
        sender=creator_address, 
        sp=sugParams, 
        total=1, 
        decimals=0, 
        default_frozen=False,
        unit_name=asset_unit_name,
        asset_name=asset_name,
        url="ipfs:://QmWEH9wMbF67t33j8ZX81ZFutyW2t96BgYU61SB16RyK4L#arc3_"
    )

    signTxn = txn.sign(creator_private_key)

    txid = algod_client.send_transaction(signTxn)

    # wait for confirmation
    TxnRes = transaction.wait_for_confirmation(algod_client, txid, 4)
    CrtAst = TxnRes["asset-index"]

    return CrtAst  
#confirmed transaction's asset id should be returned


def transferNFT(algod_client, creator_address, creator_private_key, receiver_address, receiver_private_key, asset_id):
    sugParams = algod_client.suggested_params()

    OTxn = transaction.AssetOptInTxn(
        receiver_address, 
        sp=sugParams, 
        index = asset_id
    )
       
    newsugParams = copy.deepcopy(sugParams)
    newsugParams.fee = 2 * sugParams.min_fee
    newsugParams.flat_fee = True

    FTxn = transaction.PaymentTxn(
        sender=creator_address, 
        sp= newsugParams, 
        receiver=receiver_address, 
        amt=200_000
    )

    newsugParams2 = copy.deepcopy(sugParams)
    newsugParams2.fee = 0
    newsugParams2.flat_fee = True

    ATxn = transaction.AssetTransferTxn(
        sender=creator_address, 
        sp=newsugParams2, 
        receiver=receiver_address, 
        amt=1, 
        index=asset_id
    )

    txns = [FTxn, OTxn, ATxn]
    txnGroup = transaction.assign_group_id(txns=txns)
    signedTxns = [
        txns[0].sign(creator_private_key),
        txns[1].sign(receiver_private_key),
        txns[2].sign(creator_private_key)
    ]

    transactRes = algod_client.send_transactions(signedTxns)
    update_result = transaction.wait_for_confirmation(algod_client, transactRes, 4)

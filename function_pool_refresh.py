import io
import json
import logging

import sys
#import fdk
import os
import oci
import subprocess
import time

from fdk import response

compartment_ocid = os.environ['compartment_ocid']

instance_pool_ocid = os.environ['instance_pool_ocid']

# log_levels  includes DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
LOGGER.addHandler(stream_handler)


#compartment_ocid = subprocess.getoutput("curl -H 'Authorization: Bearer Oracle' -L http://169.254.169.254/opc/v2/instance/compartmentId 2>/dev/null")
#compartment_ocid = "ocid1.tenancy.oc1..aaaaaaaa7gvqxsvrdwwbdcjlqkymmjbvjyaxnpzkqh7dlvca6w5dv5zxyjea"
#print(compartment_ocid)

#instance_pool = subprocess.getoutput("curl -H 'Authorization: Bearer Oracle' -L http://169.254.169.254/opc/v2/instance/instancePoolId 2>/dev/null")
#instance_pool_ocid = "ocid1.instancepool.oc1.iad.aaaaaaaagl3ruv4wascz3ilw5airn6kevujakuhtyve3hb3si7l72gprafyq"
#print(instance_pool_ocid)

#print(f'compartment id is : {compartment_ocid}')
#print(f'instance_pool id is : {instance_pool_ocid}')

# initialize service client with OCI python SDK
#signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
signer =  oci.auth.signers.get_resource_principals_signer()
#monitoring_client = oci.monitoring.MonitoringClient(config={}, signer=signer, service_endpoint=service_endpoint)
# Initialize service client with default config file
core_client = oci.core.ComputeManagementClient(config={}, signer=signer)
#terminate_client = oci.core.ComputeClient(config={}, signer=signer)

####################################################################################
def log_event(event):
    """Logs event information for debugging"""
    LOGGER.info("====================================================")
    LOGGER.info(event)
    LOGGER.info("====================================================")
####################################################################################
def list_instances(compartment_ocid, instance_pool_ocid):
    """ 
    Retrieve list of instances under the specified pool
    """
    try:
        list_instance_pool_instances_response = core_client.list_instance_pool_instances(
            compartment_id=compartment_ocid,
            instance_pool_id=instance_pool_ocid
        )
        pool_data = list_instance_pool_instances_response.data
        instance_ocids = [instance.id for instance in pool_data if instance.state == "Running"]
        return instance_ocids
    except oci.exceptions.ServiceError as se:
        LOGGER.error(f"Error: {se}")
        return []

####################################################################################
def pool_lifecycle_state(instance_pool_ocid):

    try:
        get_instance_pool_response = core_client.get_instance_pool(
            instance_pool_id=instance_pool_ocid)
            # Get the data from response
        get_pool_data = get_instance_pool_response.data
        #print(get_instance_pool_response.data)
        pool_lifecycle_status = get_pool_data.lifecycle_state
        print(f'instance_pool_lifecycle_state :: {pool_lifecycle_status}')
        return pool_lifecycle_status
    except oci.exceptions.ServiceError as se:
        LOGGER.error(f"Error: {se}")
        return []
    

####################################################################################
# Send the request to service, some parameters are not required, see API
# doc for more info

def detach_instance_pool(compartment_ocid, instance_pool_ocid):

    """
    This function is for detaching instance from pool 
    
    """
    try:
        instance_ocids = list_instances(compartment_ocid, instance_pool_ocid)
        print(f'Runing from Detach function for {instance_ocids}')

        for index , instance_ocid in enumerate(instance_ocids, start = 0):
            #print(f'Instance id is : {instance_ocid}')
            #print(f'Index ID is : {index}')

            detach_instance_pool_instance_response = core_client.detach_instance_pool_instance(
                instance_pool_id=instance_pool_ocid,
                detach_instance_pool_instance_details=oci.core.models.DetachInstancePoolInstanceDetails(
                    instance_id=instance_ocids[index],
                    is_decrement_size=False,
                    is_auto_terminate=True),
                #opc_retry_token="EXAMPLE-opcRetryToken-Value"
                )

            # Get the data from response
            #print(detach_instance_pool_instance_response.headers)
            log_event(detach_instance_pool_instance_response.headers)

            #get_instance_pool_response = core_client.get_instance_pool(
            #instance_pool_id=instance_pool)

            # Get the data from response
            #get_pool_data = get_instance_pool_response.data
            #print(get_instance_pool_response.data)
            #pool_lifecycle_status = pool_lifecycle_state()

            #while pool_lifecycle_status != "Running":
            #    print(f'Sleeping for 15 seconds')
            #    time.sleep(15)
            #    pool_lifecycle_status = pool_lifecycle_state()
            while True: 
                pool_lifecycle_status = pool_lifecycle_state(instance_pool_ocid)
                log_event(pool_lifecycle_status)
                if pool_lifecycle_status == "RUNNING":
                    break

                print("........................./n", end="", flush=True)
                time.sleep(15)

    except oci.exceptions.ServiceError as se:
        LOGGER.error(f"Error: {se}")
        return [] 

            

####################################################################################

def handler(ctx, data: io.BytesIO = None):
    #log_event(data)
    #print(f'{data}')
    try:
        #body = json.loads(data.getvalue())
        #compartment_ocid = body.get("compartment_ocid")
        #instance_pool_ocid = body.get("instance_pool_ocid")
        if not compartment_ocid or not instance_pool_ocid:
            return response.Response(
                ctx,
                response_data=json.dumps({"error": "Compartment OCID and instance pool OCID are required"}),
                headers={"Content-Type": "application/json"},
                status_code=400
            )

        instance_ocids = list_instances(compartment_ocid, instance_pool_ocid)
        #print(instance_ocids)
        #log_event(instance_ocids)
        detach_pool_res = detach_instance_pool(compartment_ocid, instance_pool_ocid)
        log_event(detach_pool_res)


    except Exception as ex:
        LOGGER.error(f"Error: {ex}")
        return response.Response(
            ctx,
            response_data=json.dumps({"error": str(ex)}),
            headers={"Content-Type": "application/json"},
            status_code=500
        )

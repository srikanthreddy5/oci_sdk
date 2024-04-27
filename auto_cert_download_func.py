"""certificate-download"""
import logging
import json
import io
import oci
from fdk import response
import sys
import os

# Work in progress

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
LOGGER.addHandler(stream_handler)

def certficiate_download(
        cert_ocid,
        download_type):
    
    """Download Certificate with/without Private Key.

    Keyword arguments:
    cert_ocid -- The OCID of the certificate
    download_type -- Allowed values are: “CERTIFICATE_CONTENT_PUBLIC_ONLY”, “CERTIFICATE_CONTENT_WITH_PRIVATE_KEY”
    """
    # Initialize service client with default config file
    signer = oci.auth.signers.get_resource_principals_signer()
    certificates_management_client = oci.certificates.CertificatesClient(
        config={}, signer=signer)
    try:
        download_cert = certificates_management_client.get_certificate_bundle(
            certificate_id=cert_ocid,
            certificate_bundle_type=download_type
        )
        return download_cert.data
        #clean up output
    except oci.exceptions.ServiceError as e:
        return f"{e}"
    # Need to add better verfication

def handler(ctx, data: io.BytesIO = None):
    """default hander function"""

    try:
        body = json.loads(data.getvalue())
        cert_ocid = body.get("cert_ocid")
        cert_type = body.get("cert_type")
    except ValueError as ex:
        logging.getLogger().error(
            "Error parsing input. Possibly missing input values: %s", str(ex)
        )

    LOGGER.info("cert_ocid: %s", cert_ocid)
    LOGGER.info("cert_type: %s", cert_type)

    if cert_type == "internal":
        download_type = "CERTIFICATE_CONTENT_WITH_PRIVATE_KEY"
        LOGGER.debug(f"certificate_bundle_type: {download_type}")
    else:
        download_type = "CERTIFICATE_CONTENT_PUBLIC_ONLY"
        LOGGER.debug(f"certificate_bundle_type: {download_type}")
    resp = certficiate_download(
        cert_ocid,
        download_type
        )

    return response.Response(
        ctx,
        response_data=resp,
        headers={"Content-Type": "application/json"},
    )

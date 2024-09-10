# Sets GCP project then Builds Docker container
# 
# Example run command: 
# python deploy.py -p {projectid} -r {region} -i {image name} -s {service name}

import argparse
import subprocess

def main():
    # Parse Args
    parser = argparse.ArgumentParser(description='Deploy a Docker container')
    
    parser.add_argument('-p', '--project', required=True, help='GCP Project ID')
    parser.add_argument('-r', '--region', required=True, help='GCP Region')
    parser.add_argument('-i', '--image', required=True, help='Docker Image Name')
    parser.add_argument('-s', '--service', required=True, help='Cloud Run Service Name')
    
    args = parser.parse_args()

    # Set the GCP project
    subprocess.run(['gcloud', 'config', 'set', 'project', args.project], check=True)

    # Build the Docker container using command line params
    subprocess.run([
        'gcloud', 'builds', 'submit',
        '--region=' + args.region,
        '--config=cloudbuild.yaml',
        '--substitutions=_PROJECT_ID={},_IMAGE_NAME={},_SERVICE_NAME={},_REGION={}'.format(
            args.project, args.image, args.service, args.region
        )
    ], check=True)

if __name__ == '__main__':
    main()

# ArgoCD Configuration Documentation

## Overview
This directory contains the ArgoCD application manifests for deploying the VorgabenUI application and its dependencies to Kubernetes.

## Files

### Application Manifests

#### `001_pvc.yaml`
- **Purpose**: PersistentVolumeClaim for Django application data
- **Storage**: 2Gi storage with ReadWriteMany access mode
- **Storage Class**: Uses NFS storage class for shared storage across multiple pods
- **Namespace**: vorgabenui

#### `deployment.yaml`
- **Purpose**: Main application deployment configuration
- **Contains**: Django application container, environment variables, resource limits
- **Replicas**: Configurable replica count for high availability

#### `ingress.yaml`
- **Purpose**: External access configuration
- **Host**: Configurable hostname for the application
- **TLS**: SSL/TLS termination configuration
- **Backend**: Routes traffic to the Django application service

#### `nfs-pv.yaml`
- **Purpose**: PersistentVolume definition for NFS storage
- **Server**: 192.168.17.199
- **Path**: /mnt/user/vorgabenui
- **Access**: ReadWriteMany for multi-pod access
- **Reclaim Policy**: Retain (data preserved after PVC deletion)

#### `nfs-storageclass.yaml`
- **Purpose**: StorageClass definition for NFS volumes
- **Provisioner**: kubernetes.io/no-provisioner (static provisioning)
- **Volume Expansion**: Enabled for growing storage capacity
- **Binding Mode**: Immediate (binds PV to PVC as soon as possible)

#### `diagrammer.yaml`
- **Purpose**: Deployment configuration for the diagram generation service
- **Function**: Handles diagram creation and caching for the application

## NFS Storage Configuration

### Prerequisites
1. NFS server must be running at 192.168.17.199
2. The directory `/mnt/user/vorgabenui` must exist and be exported
3. Kubernetes nodes must have NFS client utilities installed
4. For MicroK8s: `microk8s enable nfs`

## MicroK8s Addons Required

### Required Addons
Enable the following MicroK8s addons before deployment:

```bash
# Enable storage and NFS support
sudo microk8s enable storage
sudo microk8s enable nfs

# Enable ingress for external access
sudo microk8s enable ingress

# Enable DNS for service discovery
sudo microk8s enable dns

# Optional: Enable metrics for monitoring
sudo microk8s enable metrics-server
```

### Addon Descriptions

#### `storage`
- **Purpose**: Provides default storage class for persistent volumes
- **Required for**: Basic PVC functionality
- **Note**: Works alongside our custom NFS storage class

#### `nfs`
- **Purpose**: Installs NFS client utilities on all MicroK8s nodes
- **Required for**: Mounting NFS volumes in pods
- **Components**: Installs `nfs-common` package with mount helpers

#### `ingress`
- **Purpose**: Provides Ingress controller for external HTTP/HTTPS access
- **Required for**: `ingress.yaml` to function properly
- **Implementation**: Uses NGINX Ingress Controller

#### `dns`
- **Purpose**: Provides DNS service for service discovery within cluster
- **Required for**: Inter-service communication
- **Note**: Usually enabled by default in MicroK8s

#### `metrics-server` (Optional)
- **Purpose**: Enables resource usage monitoring
- **Required for**: `kubectl top` commands and HPA (Horizontal Pod Autoscaling)
- **Recommended for**: Production monitoring

### Addon Verification
After enabling addons, verify they are running:

```bash
# Check addon status
microk8s status

# Check pods in kube-system namespace
microk8s kubectl get pods -n kube-system

# Check storage classes
microk8s kubectl get storageclass

# Check ingress controller
microk8s kubectl get pods -n ingress
```

### Troubleshooting Addons

#### NFS Addon Issues
```bash
# Check if NFS utilities are installed
which mount.nfs

# Manually install if addon fails
sudo apt update && sudo apt install nfs-common

# Restart MicroK8s after manual installation
sudo microk8s restart
```

#### Ingress Issues
```bash
# Check ingress controller pods
microk8s kubectl get pods -n ingress

# Check ingress services
microk8s kubectl get svc -n ingress

# Test ingress connectivity
curl -k https://your-domain.com
```

#### Storage Issues
```bash
# List available storage classes
microk8s kubectl get storageclass

# Check default storage class
microk8s kubectl get storageclass -o yaml
```

### Storage Architecture
- **Storage Class**: `nfs` - Static provisioning for NFS shares
- **Persistent Volume**: Pre-provisioned PV pointing to NFS server
- **Persistent Volume Claim**: Claims the NFS storage for application use
- **Access Mode**: ReadWriteMany allows multiple pods to access the same data

### NFS Server Setup
On the NFS server (192.168.17.199), ensure the following:

```bash
# Create the shared directory
sudo mkdir -p /mnt/user/vorgabenui
sudo chmod 755 /mnt/user/vorgabenui

# Add to /etc/exports
echo "/mnt/user/vorgabenui *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# Export the directory
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
```

## Deployment Order

1. **StorageClass** (`nfs-storageclass.yaml`) - Defines NFS storage class
2. **PersistentVolume** (`nfs-pv.yaml`) - Creates the NFS volume
3. **PersistentVolumeClaim** (`001_pvc.yaml`) - Claims storage for application
4. **Application Deployments** (`deployment.yaml`, `diagrammer.yaml`) - Deploy application services
5. **Ingress** (`ingress.yaml`) - Configure external access

## Configuration Notes

### Namespace
All resources are deployed to the `vorgabenui` namespace.

### Storage Sizing
- Current allocation: 2Gi
- Volume expansion is enabled through the StorageClass
- Monitor usage and adjust PVC size as needed

### Access Control
- NFS export uses `no_root_squash` for container root access
- Ensure proper network security between Kubernetes nodes and NFS server
- Consider implementing network policies for additional security

## Troubleshooting

### Common Issues

#### Mount Failures
- **Error**: "bad option; for several filesystems you might need a /sbin/mount.<type> helper program"
- **Solution**: Install NFS client utilities or enable NFS addon in MicroK8s

#### Permission Issues
- **Error**: Permission denied when accessing mounted volume
- **Solution**: Check NFS export permissions and ensure `no_root_squash` is set

#### Network Connectivity
- **Error**: Connection timeout to NFS server
- **Solution**: Verify network connectivity and firewall rules between nodes and NFS server

### Debug Commands
```bash
# Check PVC status
kubectl get pvc -n vorgabenui

# Check PV status
kubectl get pv

# Describe PVC for detailed information
kubectl describe pvc django-data-pvc -n vorgabenui

# Check pod mount status
kubectl describe pod <pod-name> -n vorgabenui
```

## Maintenance

### Backup Strategy
- The NFS server should have regular backups of `/mnt/user/vorgabenui`
- Consider snapshot capabilities if using enterprise NFS solutions

### Monitoring
- Monitor NFS server performance and connectivity
- Track storage usage and plan capacity upgrades
- Monitor pod restarts related to storage issues

### Updates
- When updating storage configuration, update PV first, then PVC
- Test changes in non-production environment first
- Ensure backward compatibility when modifying NFS exports
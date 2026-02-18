# Infrastructure as Code (IaC)

This directory contains Azure Bicep templates for deploying the AI Agent Starter infrastructure.

## 📁 Structure

```
infra/
├── main.bicep                  # Main Bicep template
├── dev.parameters.json         # Development environment parameters
├── staging.parameters.json     # Staging environment parameters
└── production.parameters.json  # Production environment parameters
```

## 🏗️ Resources Deployed

The Bicep template deploys the following Azure resources:

1. **Container Registry** - Stores Docker images
2. **Container Apps Environment** - Managed environment for container apps
3. **Container App** - Hosts the AI agent application
4. **Log Analytics Workspace** - Centralized logging
5. **Application Insights** - Application monitoring (optional)
6. **Managed Identity** - Secure identity for accessing resources

## 🚀 Deployment Options

### Option 1: GitHub Actions (Recommended)

Use the automated workflow:

1. **Navigate to Actions** → `Infrastructure - Deploy to Azure`
2. **Click "Run workflow"**
3. **Select environment**: dev, staging, or production
4. **Select action**: deploy or destroy

The workflow will:
- Validate the Bicep template
- Run what-if analysis
- Deploy the infrastructure
- Output resource information
- Estimate costs

### Option 2: Azure CLI

#### Prerequisites

```bash
# Install Azure CLI
winget install Microsoft.AzureCLI

# Install Bicep
az bicep install

# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"
```

#### Deploy to Development

```bash
# Create resource group
az group create \
  --name ai-agent-starter-dev-rg \
  --location eastus

# Deploy infrastructure
az deployment group create \
  --name infra-deploy-$(date +%Y%m%d-%H%M%S) \
  --resource-group ai-agent-starter-dev-rg \
  --template-file infra/main.bicep \
  --parameters @infra/dev.parameters.json \
  --parameters azureProjectEndpoint="your-azure-ai-endpoint" \
  --parameters modelDeploymentName="gpt-4"
```

#### Deploy to Staging

```bash
# Create resource group
az group create \
  --name ai-agent-starter-staging-rg \
  --location eastus

# Deploy infrastructure
az deployment group create \
  --name infra-deploy-$(date +%Y%m%d-%H%M%S) \
  --resource-group ai-agent-starter-staging-rg \
  --template-file infra/main.bicep \
  --parameters @infra/staging.parameters.json \
  --parameters azureProjectEndpoint="your-azure-ai-endpoint" \
  --parameters modelDeploymentName="gpt-4"
```

#### Deploy to Production

```bash
# Create resource group
az group create \
  --name ai-agent-starter-production-rg \
  --location eastus

# Deploy infrastructure
az deployment group create \
  --name infra-deploy-$(date +%Y%m%d-%H%M%S) \
  --resource-group ai-agent-starter-production-rg \
  --template-file infra/main.bicep \
  --parameters @infra/production.parameters.json \
  --parameters azureProjectEndpoint="your-azure-ai-endpoint" \
  --parameters modelDeploymentName="gpt-4"
```

### Option 3: Azure Portal

1. Navigate to **Azure Portal** → **Create a resource**
2. Search for **Template deployment (deploy using custom templates)**
3. Click **Build your own template in the editor**
4. Copy and paste the contents of `main.bicep`
5. Fill in the required parameters
6. Click **Review + Create**

## 🔍 Validation

### Validate Bicep Template

```bash
# Build (validates syntax)
az bicep build --file infra/main.bicep

# What-if analysis (shows what will change)
az deployment group what-if \
  --resource-group ai-agent-starter-dev-rg \
  --template-file infra/main.bicep \
  --parameters @infra/dev.parameters.json \
  --parameters azureProjectEndpoint="endpoint" \
  --parameters modelDeploymentName="gpt-4"
```

### Test Deployment

```bash
# Get deployment outputs
az deployment group show \
  --name your-deployment-name \
  --resource-group ai-agent-starter-dev-rg \
  --query properties.outputs

# Test container app
CONTAINER_APP_URL=$(az deployment group show \
  --name your-deployment-name \
  --resource-group ai-agent-starter-dev-rg \
  --query properties.outputs.containerAppUrl.value \
  --output tsv)

curl "$CONTAINER_APP_URL/health"
```

## 📊 Environment Configurations

### Development
- **CPU**: 0.5 cores
- **Memory**: 1 GB
- **Min Replicas**: 0 (scales to zero)
- **Max Replicas**: 2
- **Cost**: ~$40-80/month

### Staging
- **CPU**: 1.0 cores
- **Memory**: 2 GB
- **Min Replicas**: 1
- **Max Replicas**: 5
- **Cost**: ~$80-150/month

### Production
- **CPU**: 2.0 cores
- **Memory**: 4 GB
- **Min Replicas**: 2
- **Max Replicas**: 10
- **Zone Redundancy**: Enabled
- **Cost**: ~$200-400/month

## 🔧 Customization

### Modify Parameters

Edit the `.parameters.json` files to customize:

```json
{
  "parameters": {
    "cpuCore": {
      "value": "1.0"  // CPU cores
    },
    "memorySize": {
      "value": "2Gi"  // Memory size
    },
    "minReplicas": {
      "value": 1      // Minimum replicas
    },
    "maxReplicas": {
      "value": 5      // Maximum replicas
    }
  }
}
```

### Add Custom Resources

Edit `main.bicep` to add additional resources:

```bicep
// Example: Add Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'ai-agent-kv-${environment}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
  }
}
```

## 🗑️ Cleanup

### Delete a Single Environment

```bash
# Using Azure CLI
az group delete --name ai-agent-starter-dev-rg --yes --no-wait

# Using GitHub Actions
# Actions → Infrastructure - Deploy to Azure → Run workflow
# Select environment and action: "destroy"
```

### Delete All Environments

```bash
# Delete all resource groups
az group list --query "[?tags.Project=='ai-agent-starter'].name" -o tsv | \
  xargs -I {} az group delete --name {} --yes --no-wait
```

## 📝 Outputs

After successful deployment, the following outputs are available:

| Output | Description |
|--------|-------------|
| `containerAppUrl` | Full HTTPS URL of the container app |
| `containerAppFqdn` | Fully qualified domain name |
| `containerRegistryName` | Name of the container registry |
| `containerRegistryLoginServer` | Login server for the registry |
| `managedIdentityId` | Resource ID of the managed identity |
| `logAnalyticsWorkspaceId` | Resource ID of the Log Analytics workspace |
| `appInsightsConnectionString` | Application Insights connection string |

### Retrieve Outputs

```bash
# Get all outputs
az deployment group show \
  --name your-deployment-name \
  --resource-group ai-agent-starter-dev-rg \
  --query properties.outputs

# Get specific output
az deployment group show \
  --name your-deployment-name \
  --resource-group ai-agent-starter-dev-rg \
  --query properties.outputs.containerAppUrl.value \
  --output tsv
```

## 🔐 Security Best Practices

1. **Secrets Management**
   - Store sensitive values in Azure Key Vault
   - Use managed identities instead of connection strings
   - Rotate secrets regularly

2. **Network Security**
   - Enable private endpoints for production
   - Use Azure Firewall for egress control
   - Implement DDoS protection

3. **Access Control**
   - Use Azure RBAC for resource access
   - Enable Azure AD authentication
   - Implement least privilege principle

4. **Monitoring**
   - Enable diagnostic settings
   - Set up alerts for critical metrics
   - Review security recommendations

## 📈 Monitoring

### View Logs

```bash
# Container app logs
az containerapp logs show \
  --name ai-agent-starter-dev \
  --resource-group ai-agent-starter-dev-rg \
  --follow

# Query Log Analytics
az monitor log-analytics query \
  --workspace your-workspace-id \
  --analytics-query "ContainerAppConsoleLogs_CL | take 100"
```

### View Metrics

```bash
# Get metrics
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.App/containerApps/{app-name} \
  --metric Requests
```

## 🆘 Troubleshooting

### Deployment Fails

```bash
# Check deployment status
az deployment group show \
  --name your-deployment-name \
  --resource-group ai-agent-starter-dev-rg

# View error details
az deployment operation group list \
  --name your-deployment-name \
  --resource-group ai-agent-starter-dev-rg
```

### Container App Not Starting

```bash
# Check container app status
az containerapp show \
  --name ai-agent-starter-dev \
  --resource-group ai-agent-starter-dev-rg

# View revision status
az containerapp revision list \
  --name ai-agent-starter-dev \
  --resource-group ai-agent-starter-dev-rg
```

## 💰 Cost Optimization

1. **Scale to Zero**: Enable for dev/staging environments
2. **Right-size Resources**: Match CPU/memory to workload
3. **Use Basic SKU**: For non-production Container Registry
4. **Delete When Not Needed**: Destroy dev environments overnight
5. **Monitor Usage**: Set up budget alerts

## 🔗 Related Documentation

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Container Registry Documentation](https://learn.microsoft.com/azure/container-registry/)
- [GitHub Actions for Azure](https://docs.github.com/actions/deployment/deploying-to-azure)

## 📞 Support

For issues or questions:
1. Check [Azure Container Apps troubleshooting](https://learn.microsoft.com/azure/container-apps/troubleshooting)
2. Review deployment logs in GitHub Actions
3. Check Azure Portal for resource health
4. Open an issue in the repository

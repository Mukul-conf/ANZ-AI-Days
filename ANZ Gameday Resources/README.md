<div align="center" padding=25px>
    <img src="images/confluent.png" width=50% height=200% >
</div>

# <div align="center">Quick Guide to setup Confluent cloud resources</div>
<br>

## <a name="step-1"></a>Log into Confluent Cloud

1. Log into [Confluent Cloud](https://confluent.cloud) and enter your email and password.

<div align="center" padding=25px>
    <img src="images/login.png">
</div>

2. If you are logging in for the first time, you will see a self-guided wizard that walks you through spinning up a cluster. Please minimize this as you will walk through those steps in this workshop. 

***

## <a name="step-2"></a>Create an Environment and Cluster

An environment contains clusters and its deployed components such as Apache Flink, Connectors, ksqlDB, and Schema Registry. You have the ability to create different environments based on your company's requirements. For example, you can use environments to separate Development/Testing, Pre-Production, and Production clusters. 

1. Click **+ Add Environment**. Specify an **Environment Name** and Click **Create**. 

>**Note:** There is a *default* environment ready in your account upon account creation. You can use this *default* environment for the purpose of this workshop if you do not wish to create an additional environment.

<div align="center" padding=25px>
    <img src="images/environment.png">
</div>

2. Now that you have an environment, click **Create Cluster**. 

> **Note:** Confluent Cloud clusters are available in 5 types: Basic, Standard, Enterprise , Dedicated and Freight. Basic is intended for development use cases so you will use that for the workshop. Basic clusters only support single zone availability. Standard , Enterprise, Dedicated and Freight clusters are intended for production use and support Multi-zone deployments. If you are interested in learning more about the different types of clusters and their associated features and limits, refer to this [documentation](https://docs.confluent.io/current/cloud/clusters/cluster-types.html).

3. Chose the **Basic** cluster type. 

<div align="center" padding=25px>
    <img src="images/cluster-type.png">
</div>

4. Click **Begin Configuration**. 
5. Choose AWS as preferred Cloud Provider, region (us-east-1), and availability zone. 
6. Specify a **Cluster Name**. For the purpose of this lab, any name will work here. 

<div align="center" padding=25px>
    <img src="images/aws-create-cluster.png" >
</div>

7. View the associated *Configuration & Cost*, *Usage Limits*, and *Uptime SLA* information before launching. 
8. Click **Launch Cluster**. 

***

## <a name="step-3"></a>Create a Flink Compute Pool

1. On the navigation menu, select **Flink** and click **Create Compute Pool**.

<div align="center" padding=25px>
    <img src="images/create-flink-pool-1.png">
</div>

2. Select **Region** and then **Continue**. (You have to use the region where the cluster was created in the previous step)
<div align="center" padding=25px>
    <img src="images/aws-create-flink-pool-1.png">
</div>

3. Name you Pool Name and set the capacity units (CFUs) to **10**. Click **Finish**.

<div align="center" padding=25px>
    <img src="images/aws-create-flink-pool-2.png">
</div>

> **Note:** The capacity of a compute pool is measured in CFUs. Compute pools expand and shrink automatically based on the resources required by the statements using them. A compute pool without any running statements scale down to zero. The maximum size of a compute pool is configured during creation. 

4. Flink Compute pools will be ready shortly. You can click **Open SQL workspace** when the pool is ready to use.

5. Change your workspace name by clicking **settings button**. Click **Save changes** after you update the workspace name.

<div align="center" padding=25px>
    <img src="images/aws-flink-workspace-1.png">
</div>

6. Set the Catalog as your environment name.

<div align="center" padding=25px>
    <img src="images/aws-flink-workspace-2.png">
</div>

7. Set the Database as your cluster name.

<div align="center" padding=25px>
    <img src="images/aws-flink-workspace-3.png">
</div>

***

## <a name="step-4"></a>Creates Topic and Walk Through Cloud Dashboard

1. On the navigation menu, you will see **Cluster Overview**. 

> **Note:** This section shows Cluster Metrics, such as Throughput and Storage. This page also shows the number of Topics, Partitions, Connectors, and ksqlDB Applications.

2. Click on **Cluster Settings**. This is where you can find your *Cluster ID, Bootstrap Server, Cloud Details, Cluster Type,* and *Capacity Limits*.
3. On the same navigation menu, select **Topics** and click **Create Topic**. 
4. Enter **shoes_orders** as the topic name, **3** as the number of partitions, skip the data contract and then click **Create with defaults**.'

<div align="center" padding=25px>
    <img src="images/create-topic.png">
</div>

5. Repeat the previous step and create a second topic name **shoes_clickstream** and **3** as the number of partitions and skip the data contract.

> **Note:** Topics have many configurable parameters. A complete list of those configurations for Confluent Cloud can be found [here](https://docs.confluent.io/cloud/current/using/broker-config.html). If you are interested in viewing the default configurations, you can view them in the Topic Summary on the right side. 

7. After topic creation, the **Topics UI** allows you to monitor production and consumption throughput metrics and the configuration parameters for your topics. When you begin sending messages to Confluent Cloud, you will be able to view those messages and message schemas.

***

## <a name="step-5"></a>Create an API Key

1. Open the cluster page.
2. Click **API Keys** in the menu under *Cluster Overview*.
3. Click **Create Key** in order to create your first API Key. If you have an existing API Key, click **+ Add Key** to create another API Key.

<div align="center" padding=25px>
    <img src="images/create-apikey-updated.png">
</div>

4. Select **My account** and then click **Next**.
5. Enter a description for your API Key (e.g. `API Key to source data from connectors`).

<div align="center" padding=25px>
    <img src="images/create-apikey-download.png">
</div>

6. After creating and saving the API key, you will see this API key in the Confluent Cloud UI in the *API Keys* table. If you don't see the API key populate right away, try refreshing your browser.
***


## <a name="step-9"></a>Consume final topic and recommend shoes to customers with aws bedrock

1. Enable access to AWS Bedrock LLama 3 8B Instruct model.
   Navigate to Amazon Bedrock, Model Catalog, Filter by Meta and search for LLama 3 8B Instruct.
   
<div align="center" padding=25px>
    <img src="images/bedrock-Llama-access.png">
</div> 

 
2. Use confluent UI to create connection with bedrock. Navigate to integrations under environment.

<div align="center" padding=25px>
    <img src="images/env-integrations.png">
</div>

3. Navigate to connections and add connections.

<div align="center" padding=25px>
    <img src="images/integrations-connection.png">
</div>

4. Copy the AWS Credentials from the AWS dashboard.

<div align="center" padding=25px>
    <img src="images/aws-creds.png">
</div>

>**Note:** Alternatively, you can create a new AWS user and assign the AmazonBedrockFullAccess policy and generate the Key and secret for this user. <br> <div align="center"><img src="images/aws-bedrock-creds.png"></div>

5. Select Bedrock, add above AWS credentials and Bedrock endpoint URL:
    https://bedrock-runtime.us-east-1.amazonaws.com/model/meta.llama3-8b-instruct-v1:0/invoke
    
<div align="center" padding=25px>
    <img src="images/bedrock-int.png">
</div>

6. After creating the connection, validate if the integration is created successfully.

<div align="center" padding=25px>
    <img src="images/bedrock-int-validate.png">
</div>

7. Use the same connection to create a model in flink.

```sql
CREATE MODEL RECOMMEND_BEDROCK
INPUT (`text` VARCHAR(2147483647)) 
OUTPUT (`output` VARCHAR(2147483647)) 
WITH ( 
    'bedrock.connection' = 'bedrock-connection', 
    'bedrock.system_prompt' = 'Generate a personalized product recommendation message',
    'provider' = 'bedrock', 
    'task' = 'text_generation' 
    );
```

8. Use the bedrock model to get shoes/brands recommendation based upon the input gathered in the final topic.

```sql
SELECT * FROM personalized_recommendation_input, 
LATERAL TABLE( 
    ML_PREDICT('RECOMMEND_BEDROCK' ,'Customer Segment:' || customer_segment || 
    ' , Trending Brands:' || trending_brands || 
    ' , Trending Products:' || trending_shoes || 
    ' , \n Craft a concise, engaging message without any input and system level parameters and only give me Recommendation Message, recommending one or two relevant products or brands. Tailor the tone to match the customer’s segment and include a compelling call-to-action to drive engagement. remove any debrock specific headers and give final message which can be shown as a string.')
    );
```

```sql
CREATE TABLE Recommendations AS SELECT customer_id , output FROM personalized_recommendation_input, 
LATERAL TABLE( 
    ML_PREDICT('RECOMMEND_BEDROCK' ,'Customer Segment:' || customer_segment || 
    ' , Trending Brands:' || trending_brands || 
    ' , Trending Products:' || trending_shoes || 
    ' , \n Craft a concise, engaging message without any input and system level parameters and only give me Recommendation Message, recommending one or two relevant products or brands. Tailor the tone to match the customer’s segment and include a compelling call-to-action to drive engagement. remove any debrock specific headers and give final message which can be shown as a string.')
    );  
```

<div align="center"><img src="images/final-message.png"></div>



 <details>
      <summary><a name="step-10"></a> Embedding Generation using Flink & Bedrock (Optional)</summary>

The next step is to generate embeddings using Titan Model in AWS Bedrock.

1. First, navigate to AWS Bedrock Model Catalog and enable access to the Titan Model.
   
<div align="center" padding=25px>
    <img src="images/aws-bedrock-titan.png">
</div>

2. Copy the AWS Credentials from the AWS dashboard.

<div align="center" padding=25px>
    <img src="images/aws-creds.png" >
</div>

>**Note:** Alternatively, you can create a new AWS user and assign the AmazonBedrockFullAccess policy and generate the Key and secret for this user. <br> <div align="center"><img src="images/aws-bedrock-creds.png"></div>

3. Navigate to Environments -> Integrations -> Connections and create a Bedrock integration. 
   Endpoint: https://bedrock-runtime.us-east-1.amazonaws.com/model/amazon.titan-embed-text-v2:0/invoke
 
<div align="center" padding=25px>
    <img src="images/bedrock-titan.png">
</div>

4. Validate if the connection is created successfully.

<div align="center" padding=25px>
    <img src="images/aws-titan-validate.png">
</div>

5. Use the same connection to create a model in Flink.

```sql
CREATE MODEL RECOMMEND_BEDROCK_TITAN
INPUT (`text` VARCHAR(2147483647)) 
OUTPUT (`output` VARCHAR(2147483647)) 
WITH ( 
    'bedrock.connection' = 'bedrock-connection-titan', 
    'bedrock.input_format' = 'Generate a personalized product recommendation message',
    'provider' = 'bedrock', 
    'task' = 'embedding' 
    );
```

6. Use the bedrock model to get embeddings from topic data
```sql
SELECT `user_id`, response from(
SELECT * from shoes_clickstream, LATERAL TABLE(ML_PREDICT('RECOMMEND_BEDROCK_TITAN', `user_id`)));
```
<div align="center" padding=25px>
    <img src="images/final-embeddings.png" >
</div>
 </details>



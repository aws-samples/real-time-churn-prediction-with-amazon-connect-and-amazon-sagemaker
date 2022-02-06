  
 # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 # SPDX-License-Identifier: MIT-0
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy of this
 # software and associated documentation files (the "Software"), to deal in the Software
 # without restriction, including without limitation the rights to use, copy, modify,
 # merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 # permit persons to whom the Software is furnished to do so.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 # INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 # PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 # HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 # OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 # SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# This code snippet is lightly modified from that provided by AWS Secrets Manager during secrets creation.

import boto3
import base64
from botocore.exceptions import ClientError
import json
import matplotlib.pyplot as plt
import graphviz
import sagemaker
from sagemaker.feature_store.feature_group import FeatureGroup
from typing import Dict

def get_secret(secret_name, region_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response
    except ClientError as e:
        print(e)
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        else:
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        print('now in else')
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            print(secret)
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])


# Extract training and validation AUC values from the results returned by
# method describe_training_job()

def get_auc_from_metrics(response, metric_type):
    for x in range(len(response['FinalMetricDataList'])):
        if metric_type in response['FinalMetricDataList'][x].values():
            return x


# Functions for model feature exploration

def plot_feature_importance(booster, f, maxfeats = 15):
    from xgboost import plot_importance
    res = {k:round(v, 2) for k, v in booster.get_score(importance_type = f).items()}
    gain_plot = plot_importance(res,
                                max_num_features = maxfeats,
                                importance_type = f,
                                title = 'Feature Importance: ' + f,
                                color = "#4daf4a")
    plt.show()


# Calculate tree depth. Adapted the code from here
# https://stackoverflow.com/questions/29005959/depth-of-a-json-tree to Python 3.

def calculate_tree_depth(tree_dict):
    # input: single tree as a dictionary
    # output: depth of the tree
    if 'children' in tree_dict:
        return 1 +  max([0] + list(map(calculate_tree_depth, tree_dict['children'])))
    else:
        return 1

def get_depths_as_list(all_trees):
    # input: list of all trees, generated by xgboost's get_dump in json format
    # output: list of the same length as all_trees where each element contains
    # the depth of a tree
    # list to store the depth of each tree
    tree_depth = []
    for i in range(len(all_trees)):
        tree = json.loads(all_trees[i])
        tree_depth.append(calculate_tree_depth(tree))
    return tree_depth

def calculate_list_unique_elements(input_list):
    # calculate number of unique elements in a list
    # input: list
    # output: dictionary. Keys: unique elements, values: their count
    res = dict()
    for i in input_list:
        if i in res:
            res[i] += 1
        else:
            res[i] = 1
    return res


def find_feature(tree_dict, feature):
    # input:
    #    tree_dict: single tree as a dictionary
    #    feature: feature name, str
    # output: 0 if a feature is not a split, 1 if the feature is a split at any node
    if "split" in tree_dict:
        if tree_dict["split"] == feature:
            return 1
        else:
            for child in tree_dict["children"]:
                res = find_feature(child, feature)
                if res != 0:
                    return res
            return 0
    else:
        return 0

# find all trees that have a feature
def find_all_trees_with_feature(all_trees, feature):
    # input:
    #    all_trees: list of all trees, generated by xgboost's get_dump in json format
    #    feature: feature name, str
    # output: indices of trees where a feature has been found at any node
    trees_with_features = []
    for i in range(len(all_trees)):
        tree = json.loads(all_trees[i])
        if find_feature(tree, feature) == 1:
            trees_with_features.append(i)
    return trees_with_features


# given a list of features find how many trees have it
def count_trees_with_features(all_trees, feature_list):
    # input:
    #   all_trees: list of all trees, generated by xgboost's get_dump in json format
    #   feature_list: list of features
    # output: dictionary, keys = feature_list, values = number of trees where a feature has been found
    tree_count = dict()
    for i in feature_list:
        tree_count[i] = 0
    for i in feature_list:
        for j in range(len(all_trees)):
            tree = json.loads(all_trees[j])
            if find_feature(tree, i) == 1:
                tree_count[i] += 1
    return tree_count


def get_fg_info(fg_name: str, sagemaker_session: sagemaker.Session):
    boto_session = sagemaker_session.boto_session
    featurestore_runtime = sagemaker_session.sagemaker_featurestore_runtime_client
    feature_store_session = sagemaker.Session(
        boto_session=boto_session,
        sagemaker_client=sagemaker_session.sagemaker_client,
        sagemaker_featurestore_runtime_client=featurestore_runtime,
    )
    fg = FeatureGroup(name=fg_name, sagemaker_session=feature_store_session)
    return fg.athena_query()

def generate_query(dataset_dict: Dict, sagemaker_session: sagemaker.Session):
    
    customers_fg_info = get_fg_info(
        dataset_dict["customers_fg_name"],
        sagemaker_session=sagemaker_session,
    )

    label_name = dataset_dict["label_name"]
    features_names = dataset_dict["features_names"]
    training_columns = [label_name] + features_names
    training_columns_string = ", ".join(f'"{c}"' for c in training_columns)

    query_string = f"""SELECT DISTINCT {training_columns_string}
        FROM "{customers_fg_info.table_name}" 
    """
    return dict(
        catalog=claims_fg_info.catalog,
        database=claims_fg_info.database,
        query_string=query_string,
    )
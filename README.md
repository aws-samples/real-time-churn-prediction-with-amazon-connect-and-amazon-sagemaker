## Real-time Churn Prediction with Amazon Connect and Amazon SageMaker

This repository provide a demonstration of how to build a real-time customer churn prediction pipeline for contact centers using Amazon connect and Amazon SageMaker services.

## Architecture

The following is the architecture diagram for the "Real-Time churn prediction with Amazon Connect and Amazon SageMaker".

![1](Architecture.png) 

## Deployment

This solution require:

- An existing Amazon Connect instance with Contact Lens for Amazon Connect enabled
- Contact Flows enabled for "Real-Time and post call analytics" in the "Set recording and analytics behavior"
- Create three (3) Real-time Contact Lens Rules with a "Sentiment - Time period" from the "Customer" for positive, negative, and neutral sentiments for the past 15 seconds of the contact

![2](/img/clrules.png)

- Assign a contact category called PositiveSentiment, NegativeSentiment, and NeutralSentiment for each of the rules
- Add an action "Generate an EventBridge event" using the same name of the category

![3](/img/clActions.png)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.


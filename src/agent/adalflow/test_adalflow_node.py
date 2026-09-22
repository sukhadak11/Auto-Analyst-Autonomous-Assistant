from adalflow_report_node import adalflow_report_agent_node


def main():

    state = {

        "question": "Why are customers churning?",

        "data_findings": """
The dataset contains 3333 customers.
The overall churn rate is 14.5%.
Customers with more customer service calls show higher churn.
""",

        "feature_importance": [
            ("customer_service_calls", 0.421),
            ("day_mins", 0.287),
            ("international_mins", 0.164),
        ],

        "research_findings": """
Customer service interactions are commonly associated with
customer dissatisfaction and churn risk.
""",

        "prediction_result": "Not computed in this analysis.",

        "messages": [],
    }

    result = adalflow_report_agent_node(state)

    print("\n" + "=" * 60)
    print("ADALFLOW REPORT")
    print("=" * 60)

    print(result["report"])

    print("\n" + "=" * 60)
    print("MESSAGES")
    print("=" * 60)

    print(result["messages"])


if __name__ == "__main__":
    main()
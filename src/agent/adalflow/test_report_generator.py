from report_generator import AdalFlowReportGenerator


def main():

    print("=" * 60)
    print("AutoAnalyst - AdalFlow Report Agent PoC")
    print("=" * 60)

    # -------------------------------------------------
    # Create AdalFlow report generator
    # -------------------------------------------------
    generator = AdalFlowReportGenerator()

    print("\nGenerating report...\n")

    # -------------------------------------------------
    # Sample AutoAnalyst analysis results
    # -------------------------------------------------
    response = generator(
        question="Why are customers churning?",

        data_findings="""
The dataset contains 3333 customers.
The overall churn rate is 14.5%.
Customers with more customer service calls show higher churn.
""",

        feature_importance="""
customer_service_calls: 0.421
day_mins: 0.287
international_mins: 0.164
""",

        research_findings="""
Customer service interactions are commonly associated with
customer dissatisfaction and churn risk.
""",

        prediction_result="Not computed in this analysis.",
    )

    # -------------------------------------------------
    # Check response
    # -------------------------------------------------
    print("Response type:")
    print(type(response))

    print("\nParsed output type:")
    print(type(response.data))

    # -------------------------------------------------
    # Display structured result
    # -------------------------------------------------
    if response.data is not None:

        print("\n" + "=" * 60)
        print("ANSWER")
        print("=" * 60)
        print(response.data.answer)

        print("\n" + "=" * 60)
        print("RECOMMENDATION")
        print("=" * 60)
        print(response.data.recommendation)

        print("\n" + "=" * 60)
        print("KEY FINDINGS")
        print("=" * 60)

        for index, finding in enumerate(
            response.data.key_findings,
            start=1
        ):
            print(f"{index}. {finding}")

    else:

        print("\nAdalFlow could not parse the response.")

        print("\nRaw response:")
        print(response)


if __name__ == "__main__":
    main()
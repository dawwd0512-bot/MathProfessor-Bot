class Observer:

    def observe(self, results):

        report = []

        for result in results:

            if not result:
                continue


            # نتائج PlanExecutor
            if "result" in result:

                inner = result.get(
                    "result",
                    []
                )


                if isinstance(inner, list) and inner:

                    data = inner[0]


                    output = data.get(
                        "output",
                        ""
                    )


                    if isinstance(output, dict):

                        output = output.get(
                            "output",
                            output
                        )


                    report.append(
                        {
                            "tool": result.get(
                                "tool"
                            ),
                            "success": data.get(
                                "success",
                                False
                            ),
                            "summary": str(
                                output
                            )[:300]
                        }
                    )

                    continue


            # نتائج TaskExecutor القديمة
            output = result.get(
                "output",
                ""
            )


            if isinstance(output, dict):

                output = output.get(
                    "output",
                    output
                )


            report.append(
                {
                    "tool": result.get(
                        "tool"
                    ),
                    "success": result.get(
                        "success",
                        False
                    ),
                    "summary": str(
                        output
                    )[:300]
                }
            )


        return report

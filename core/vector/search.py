import math


def cosine_similarity(a, b):

    if not a or not b:
        return 0


    length = min(
        len(a),
        len(b)
    )


    dot = sum(
        a[i] * b[i]
        for i in range(length)
    )


    mag_a = math.sqrt(
        sum(
            x * x
            for x in a[:length]
        )
    )


    mag_b = math.sqrt(
        sum(
            x * x
            for x in b[:length]
        )
    )


    if mag_a == 0 or mag_b == 0:
        return 0


    return dot / (
        mag_a * mag_b
    )



class VectorSearch:


    def search(self, query_vector, items, limit=3):

        results = []


        for item in items:

            score = cosine_similarity(
                query_vector,
                item.get("vector", [])
            )


            results.append(
                {
                    "score": score,
                    "item": item
                }
            )


        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        return results[:limit]

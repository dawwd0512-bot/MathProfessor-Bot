class KnowledgeRouter:

    def __init__(
        self,
        knowledge_base,
        search_provider,
        web_reader,
        document_reader
    ):

        self.knowledge = knowledge_base
        self.search = search_provider
        self.web = web_reader
        self.documents = document_reader


    def answer_source(
        self,
        user_id,
        query
    ):

        internal = self.knowledge.search(
            user_id,
            query
        )


        web_results = self.search.search(
            query
        )


        response = {
            "internal_knowledge": internal,
            "internet_results": web_results
        }


        if self._contains_url(query):

            page = self.web.read(
                query
            )

            response["url_content"] = page


        return response



    def _contains_url(self, text):

        return (
            "http://" in text
            or
            "https://" in text
        )

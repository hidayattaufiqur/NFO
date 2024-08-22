## TODO
# top priority
- [x] save CQs to DB
- [x] get conversations by joining table conversations and message_store
- [x] Implement interaction between user and LLM through langchain for validating or revising generated CQs
- [x] Implement generated CQs storing to a database
- [x] create upload PDF handler 
- [x] create PDF handler to ectract texts out of PDF and then process 
using flair or something else to get the important terms
- [x] fix ChatHistories class implementation
- [x] create web scraping handler 
- [x] create handler to extract texts out of web scraping and then process using flair or sumn else
- [x] fix prompt to awan llm domain and scope body 
- [x] create terms table to store important terms
- [x] generate classes, object properties, and data properties out of important terms using LLM 
- [x] scope in step 3 is actually using domain within conversation 
- [x] fuse important terms and class and instance generation into the same endpoint
- [x] change the flow of authentication
- [x] consider hadnling the logic on a higher level (e.g. in the service layer)
- [x] refactor the code to make it more modular, readable, and maintainable
- [x] saved CQ should be validated instantly
- [x] add time counter for each process in terms extractor (pdf/url)
- [x] MAKE TEMRS EXTRACTOR WORK FASTER CUZ CF ONLY WILL WORK FOR 100 SECONDS

- [x] implement PUT and GET methods for important terms
- [x] implement PUT method for CQs 
- [x] update generate module endpoints in API docs
- [x] fix issue of the PDF handler not working (file not uploaded) on production
- [x] saves object and data properties to DB
- [x] create class and properties data junctions DB command and query
- [x] add logout endpoint
- [x] add create classes, object properties, and data properties endpoints
- [x] add API documentations for saving class and data properties endpoints
- [x] implement OWL file generation for the ontology system
- [x] implement add range and domain endpoints
- [x] fix bug in llmsherpa daemon 

- [ ] (optionally) add array of data properties, classes, instances to class endpoint
- [ ] change implementation of step 2 
- [ ] buat step 7 yg instances. get by conv_id sama post instances by conv_id yak

# mid priority
- [x] weigh in whether to use UUID, ULID, or instead serial as PK (or even keep serial + UUID/ULID) -> maybe watch Hussein's video
- [x] Implement logging 
- [x] restructure code (e.g. handlers to one new specific file)
- [x] Implement error handling for API calls
- [x] better error log and response per route
- [x] secure routes using oauth session key
- [x] Implement user authorization and session management

- [ ] update README
- [ ] add explanation in README to install Spacy model beforehand with this command `python -m spacy download en_core_web_sm`
- [ ] handle text chunking for AwanLLM request to be optional if the text lenght is more than a certain threshold
- [x] fix issue with LLM output format

# low priority
- [x] use poetry
- [ ] implement DB migration

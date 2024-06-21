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

- [i] saves object and data properties to DB
- [ ] user can go back to previous steps
- [ ] work on the 6th step
- [ ] work on the 7th step
- [ ] create class data junction db command and query
- [ ] consider hadnling the logic on a higher level (e.g. in the service layer)
- [ ] refactor the code to make it more modular, readable, and maintainable

# mid priority
- [x] weigh in whether to use UUID, ULID, or instead serial as PK (or even keep serial + UUID/ULID) -> maybe watch Hussein's video
- [x] Implement logging 
- [x] restructure code (e.g. handlers to one new specific file)
- [x] Implement error handling for API calls
- [x] better error log and response per route
- [x] secure routes using oauth session key
- [x] Implement user authorization and session management

- [ ] implement DB migration
- [ ] update README

# low priority
- [x] use poetry

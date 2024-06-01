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

- [ ] user can go back to previous steps

# mid priority
- [x] weigh in whether to use UUID, ULID, or instead serial as PK (or even keep serial + UUID/ULID) -> maybe watch Hussein's video
- [x] Implement logging 
- [x] restructure code (e.g. handlers to one new specific file)
- [x] Implement error handling for API calls

- [ ] better error log and response per route
- [ ] secure routes using oauth session key
- [ ] implement DB migration
- [ ] Implement user authorization and session management
- [ ] update README

# low priority
- [x] use poetry

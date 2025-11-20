from SmartSearch.model import ai_validator, ai_interviewer

# testing 
if __name__ == "__main__":
	field = "возраст"
	format = " "
	user_answer = "5 лет"

	for i in range(2):
		ai_question = ai_interviewer.create_answer(field)
		valid = ai_validator.validate_ai_question(field, ai_question['question'])
		print(ai_question)
		print(valid)
		if valid['status'] == "failed":
			res = ai_interviewer.change_answer(field, ai_question['question'], valid['issues'] )
			val = ai_validator.validate_ai_question(field, ai_question["question"])
			print("----",res, val)
		if valid['status'] == "ok":
			break

	user = ai_validator.validate_user_answer(ai_question['question'], user_answer)
	print(user)
	
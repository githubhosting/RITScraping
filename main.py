import datetime

import pandas as pd
import streamlit as st

from src.exam import micro
from src.scraper import validate_usn
from src.sis import micro
from tools import sub_lists, grade_estimates

th_props = [
	('text-align', 'left'),
	('font-weight', 'bold'),
]

td_props = [
	('text-align', 'center'),
]

headers_props = [
	('text-align', 'center'),
]

table_body = [
	('background-color', '#000'),
	("display", "inline-block")
]

styles = [
	dict(selector="th", props=th_props),
	dict(selector="td:nth-child(3)", props=td_props),
]

styles_attd = [
	dict(selector="td:nth-child(3)", props=td_props),
	dict(selector="td:nth-child(4)", props=td_props),
]

st.set_page_config(
	page_title="Calculla - GPA Calculator", page_icon="📊", layout="centered",
	initial_sidebar_state="expanded"
)


def local_css(file_name):
	with open(file_name) as f:
		st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


local_css("styles.css")

st.title("Calculla - GPA Calculator")
st.markdown(
	'Follow the instructions and see the how its calculated <a href="/Instruction_and_Working" >***Click Here*** </a>',
	unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Check CIE Marks", "Grades-Score", "Credit-CGPA", "Crack DOB", "How it works?"])
grade_to_gp = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0}


@st.cache_data
def getMetaAndMarks(year, dept, i, temp, dob):
	m1, m2 = micro(year, dept, i, temp, dob=dob, lite=True)
	return m1, m2


def tab_1():
	year = dept = i = temp = dob = None

	st.subheader("Check your CIE Marks")
	usn = st.text_input("Enter your USN").upper()

	if validate_usn(usn):
		year = int(usn[3:5]) + 2000
		dept = usn[5:7]
		i = int(usn[7:10])
		if len(usn) == 10:
			temp = False
		else:
			temp = True
		dob = st.date_input("Enter DOB", datetime.date(year - 18, 1, 1))

		get = st.button("Get Marks")
		if get:
			meta, marks = getMetaAndMarks(year, dept, i, temp, dob=dob)
			if not meta:
				st.warning("Invalid USN or DOB", icon="🚨")
			else:
				st.subheader(f"Hey {meta['name']}! 👋")
				st.write(f"")
				st.write(f"Here is your CIE Marks for Semester {meta['sem']}")

				sub_codes, sub_names, sub_attds, sub_marks, sub_creds = sub_lists(marks)

				table = pd.DataFrame(
					{"Subject": sub_names, "Marks": sub_marks},
					index=[j for j in range(1, len(sub_marks) + 1)]
				)
				st.markdown(table.style.set_table_styles(styles).to_html(), unsafe_allow_html=True)
				total_cie_marks = sum(sub_marks)
				st.subheader(f"Your Total CIE Marks: {total_cie_marks}/{len(sub_marks) * 50}")
				st.markdown(
					"""
					&nbsp;
					#### Here is your Attendance %
					"""
				)

				short_attendance = []
				for j in sub_attds:
					if j < 75: short_attendance.append({sub_names[sub_attds.index(j)]})
				attendance = [str(j) + "%" for j in sub_attds]

				table = pd.DataFrame(
					{"Subject": sub_names, "Percentage": attendance},
					index=[k for k in range(1, len(sub_marks) + 1)]
				)
				st.markdown(table.style.set_table_styles(styles_attd).to_html(), unsafe_allow_html=True)
				if short_attendance:
					st.write("")
					st.write("You have short attendance in the following subjects")
					for key in short_attendance:
						remove = str(key).replace("{'", "").replace("'}", "")
						st.warning(remove)
	elif usn:
		st.error('Invalid USN', icon="🚨")

	return year, dept, i, temp, dob


def tab_2(year, dept, i, temp, dob):
	st.title("Each Subject Scoring Criteria")
	st.write("You have to score the following marks in SEE to get the respective grade")
	sub_codes = sub_names = sub_attds = sub_marks = sub_creds = None
	if dob:
		meta, marks = getMetaAndMarks(year, dept, i, temp, dob=dob)
		if not meta:
			st.error("Invalid USN or DOB", icon="🚨")
		else:
			sub_codes, sub_names, sub_attds, sub_marks, sub_creds = sub_lists(marks)
			grade_lists = grade_estimates(
				sub_marks, sub_names,
				**{"O": 90, "A+": 80, "A": 70, "B+": 60, "B": 55, "C": 50, "P": 40, "F": 0}
			)
			table = pd.DataFrame(
				{"Subject": sub_names, "Marks": sub_marks, **grade_lists},
				index=[i for i in range(1, len(sub_marks) + 1)]
			).fillna(" ")
			st.table(table)
	else:
		st.warning("Enter your USN and DOB first", icon="⚠️")
	return sub_names, sub_creds


def tab_3(sub_names, dob, sub_creds):
	if dob and sub_creds:
		st.subheader("Enter your Predicted Grade for each subjects")

		grade_in_each = []
		for name in sub_names: grade_in_each.append(
			st.radio(name, ["O", "A+", "A", "B+", "B", "C", "P", "F"], horizontal=True))
		grade_point = [grade_to_gp[g] for g in grade_in_each]
		weighted_gp = [i * j for i, j in zip(grade_point, sub_creds)]
		total_credits_final = sum(weighted_gp)

		st.write("Based on the above grades, this will be your final credits and CGPA")
		table = pd.DataFrame({
			"Subject": sub_names, "Grade": grade_in_each, "Credits": sub_creds,
			"Grade Points": [f"{w}/{c * 10}" for w, c in zip(weighted_gp, sub_creds)]
		})
		st.table(table)

		cgpa = total_credits_final / sum(sub_creds)
		cgpa = round(cgpa, 3)
		st.subheader(f"Your CGPA is:\t " f"{cgpa}")
	else:
		st.error("Enter USN and DOB first", icon="🚨")


def home():
	with tab1:
		year_, dept_, i_, temp_, dob_ = tab_1()
	with tab2:
		subject_name_, creds_ = tab_2(year_, dept_, i_, temp_, dob_)
	with tab3:
		tab_3(subject_name_, dob_, creds_)
	with tab4:
		st.write(f"{st.experimental_user.email} Dont Have access to this page")
		if st.experimental_user.email in ['revannamrclk@email.com', 'shravanrevanna158@gmail.com',
										  'amitharun3@gmail.com']:
			st.write("Welcome to the page")
		else:
			st.write("Please contact us to get access!")
	with tab5:
		st.title("About")
		st.write("This is a simple web app to calculate your GPA based on the marks you scored")


if __name__ == '__main__':
	home()

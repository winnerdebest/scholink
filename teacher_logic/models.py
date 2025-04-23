from django.db import models

# All models import 
from stu_main.models import CustomUser, ClassSubject
from academic_main.models import Term


class SubjectGradeSummary(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subject_grade_summaries')
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.SET_NULL, related_name='grade_summaries', null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, related_name='subject_grade_summaries', null=True, blank=True)

    external_exam_score = models.FloatField(default=0)
    external_assignment_score = models.FloatField(default=0)
    external_test_score = models.FloatField(default=0)

    def get_internal_exam_average(self):
        from exams.models import StudentExamRecord
        exam_records = StudentExamRecord.objects.filter(
            student=self.student,
            exam__class_subject=self.class_subject,
            exam__term=self.term,
        )
        scores = [r.score for r in exam_records]
        return sum(scores) / len(scores) if scores else 0

    def get_internal_assignment_average(self):
        from assignments.models import StudentAssignmentRecord  
        assignment_records = StudentAssignmentRecord.objects.filter(
            student=self.student,
            assignment__class_subject=self.class_subject,
            assignment__term=self.term,
        )
        scores = [r.score for r in assignment_records]
        return sum(scores) / len(scores) if scores else 0

    @property
    def total_score(self):
        internal_exam_avg = self.get_internal_exam_average()
        internal_assignment_avg = self.get_internal_assignment_average()

        # Exams: external (30%) + internal (30%) = 60%
        exam_score = ((self.external_exam_score / 100) * 30) + ((internal_exam_avg / 100) * 30)

        # Assignments: external + internal combined, then scaled to 20%
        assignment_score = ((self.external_assignment_score + internal_assignment_avg) / 100) * 20

        # Tests: external only (20%)
        test_score = (self.external_test_score / 100) * 20

        total = exam_score + assignment_score + test_score
        return round(total, 2)

    def __str__(self):
        return f"{self.student} - {self.class_subject} - {self.term}"

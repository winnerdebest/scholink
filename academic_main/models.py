from django.db import models

class Term(models.Model):
    name = models.CharField(max_length=50)  # E.g., "First Term", "Second Term"

    def __str__(self):
        return self.name


class ActiveTerm(models.Model):
    term = models.OneToOneField(Term, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Active Term: {self.term.name}"

    @classmethod
    def get_active_term(cls):
        return cls.objects.first().term
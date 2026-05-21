from django.db import models

# Create your models here.
class SymptomCheker(models.Model):
    user = models.ForeignKey('Users.User', on_delete=models.CASCADE, related_name='symptoms', blank=True, null=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    duration_of_symptoms = models.CharField(max_length=50)
    symptoms = models.TextField()
    additional_info = models.TextField(blank=True, null=True)
    possible_conditions = models.TextField(blank=True, null=True)
    triage_urgency = models.CharField(max_length=20, blank=True, null=True)
    recommended_specialist = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Symptom Report for {self.user.first_name} {self.user.last_name} - Age: {self.age}, Gender: {self.gender}, Duration: {self.duration_of_symptoms}"
        else:
            return f"Symptom Report - Age: {self.age}, Gender: {self.gender}, Duration: {self.duration_of_symptoms}"
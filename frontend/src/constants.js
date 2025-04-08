// Activity mapping by subject
export const SUB_ACTIVITIES = {
  Math: ['Addition/Subtraction', 'Multiplication/Division', 'Word Problems', 'Mushroom Kingdom Calculations'],
  English: ['Opposites/Antonyms', 'Synonyms', 'Reading Comprehension', 'Nouns/Pronouns', 'Grammar Correction', 'Mushroom Kingdom Vocabulary']
};

// Get default sub-activity for a subject
export const getDefaultSubActivity = (subject) => {
  const subjectKey = subject.charAt(0).toUpperCase() + subject.slice(1).toLowerCase();
  return SUB_ACTIVITIES[subjectKey]?.[0] || 'Addition/Subtraction';
}; 
export type QuickAction = {
  label: string;
  prompt: string;
};

export const quickActions: QuickAction[] = [
  {
    label: "Подобрать курс",
    prompt: "Подбери курс по LLM для начинающего",
  },
  {
    label: "Сравнить тарифы",
    prompt: "Сравни курсы agents и deep-agents по цене и программе",
  },
  {
    label: "Оформить покупку",
    prompt: "Хочу оформить покупку курса agents",
  },
];

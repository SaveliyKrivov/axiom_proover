from Utils import *
from typing import List


class Prover:
    def __init__(self, axioms: List[Expression], target: Expression, output_callback=None):
        self.axioms = [simplify(axiom.to_implication_form()) for axiom in axioms]  # Список для хранения аксиом
        self.conditions = self.axioms  # Условия
        self.target = simplify(target.to_implication_form())  # Ц��ль доказательства
        self.to_prove = self.target  # Цель доказательства для обработки
        self.sequent = None
        self.output_callback = output_callback
        self.preprocessing()

    def preprocessing(self):
        self.unification()
        self.sequent = Sequent({condition: 0 for condition in self.conditions},
                               {self.to_prove: 0},
                               0)

    def unification(self):
        for i in range(len(self.conditions)):
            substitutions = unify(self.conditions[i], self.to_prove, None)
            if substitutions is not None:
                print(f"Замены при унификации: {', '.join(f'{k}: {v}' for k, v in substitutions.items())}")
                self.conditions[i] = apply_substitutions(self.conditions[i], substitutions)

    def prove(self):
        """Доказательство строится на основе создания дерева секвентов"""
        if self.sequent is None:
            return False
        # Списки для хранения секвенции, которые нужно проверить и те, что уже доказаны
        frontier = [self.sequent]  # Секвенты для проверки
        proven = {self.sequent}  # Секвенты, которые уже доказаны

        current_depth = 0
        modus_ponens_applied_expressions = set()
        deduction_applied_expressions = set()

        while True:
            # Получаем следующий секвент из списка для проверки
            old_sequent = None
            while len(frontier) > 0 and (old_sequent is None or old_sequent in proven):
                old_sequent = frontier.pop(0)  # Извлекаем первый секвент
            if old_sequent is None:
                break  # Если больше нет секвентов для проверки, выходим из цикла

            # Сброс флага при переходе на новый уровень глубины
            if old_sequent.depth != current_depth:
                current_depth = old_sequent.depth
                modus_ponens_applied_expressions.clear()
                deduction_applied_expressions.clear()

            # Выводим информацию о текущем секвенте
            output_message = f'Глубина: {old_sequent.depth}. Секвент: {old_sequent}'
            print(output_message)
            if self.output_callback:
                self.output_callback(output_message)

            # Проверяем, является ли секвент аксиоматически истинным без унификации
            if len(set(old_sequent.left.keys()) & set(old_sequent.right.keys())) > 0:
                proven.add(old_sequent)
                continue

            while True:
                # Определим с какой формулой будем работать
                left_expression = None
                left_depth = None
                for expression, depth in old_sequent.left.items():
                    if left_depth is None or left_depth > depth:
                        if not isinstance(expression, Variable):
                            left_expression = expression
                            left_depth = depth

                right_expression = None
                right_depth = None
                for expression, depth in old_sequent.right.items():
                    if right_depth is None or right_depth > depth:
                        if not isinstance(expression, Variable):
                            right_expression = expression
                            right_depth = depth

                # Определяем с какой частью секвента будем работать
                apply_left = False
                apply_right = False
                if left_expression is not None and right_expression is None:
                    apply_left = True
                if left_expression is None and right_expression is not None:
                    apply_right = True
                if left_expression is not None and right_expression is not None:
                    if left_depth < right_depth:  # Строгий знак, тк приоритетнее обработать правую часть
                        apply_left = True
                    else:
                        apply_right = True
                if left_expression is None and right_expression is None:
                    return False  # Если формул нет, не можем доказать

                # Применение левого правила
                if apply_left:
                    if isinstance(left_expression, Negation):
                        output_message = f"Перебрасываем левую часть {left_expression} в право:"
                        print(output_message)
                        if self.output_callback:
                            self.output_callback(output_message)
                        new_sequent = remove_left_negation(old_sequent, left_expression)
                        frontier.append(new_sequent)  # Добавляем новый секвент в frontier
                        break
                    if isinstance(left_expression, Implication):
                        if left_expression not in modus_ponens_applied_expressions:
                            output_message = f"Применение modus ponens к выражению {left_expression}:"
                            print(output_message)
                            modus_ponens_applied_expressions.add(left_expression)
                            if self.output_callback:
                                self.output_callback(output_message)
                        
                        new_sequents = modus_ponens(old_sequent, left_expression)
                        frontier.extend(new_sequents)  # Добавляем новые секвенты в frontier
                        break

                # Применение правого правила
                if apply_right:
                    if isinstance(right_expression, Negation):
                        output_message = f"Перебрасываем правую часть {right_expression} в левую:"
                        print(output_message)
                        if self.output_callback:
                            self.output_callback(output_message)

                        new_sequent = remove_right_negation(old_sequent, right_expression)
                        frontier.append(new_sequent)  # Добавляем новый секвент в frontier
                        break
                    if isinstance(right_expression, Implication):
                        if right_expression not in deduction_applied_expressions:
                            output_message = f"Применяем теорему о дедукции к выражению {right_expression}:"
                            print(output_message)
                            deduction_applied_expressions.add(right_expression)
                            if self.output_callback:
                                self.output_callback(output_message)
                    
                        new_sequent = deduction(old_sequent, right_expression)
                        frontier.append(new_sequent)  # Добавляем новый секвент в frontier
                        break

        # Если больше нет секвентов для доказательства, возвращаем True
        return True
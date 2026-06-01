<!-- Source PDF: https://jvgemert.github.io/writing.pdf -->

# Jan van Gemert writing guidelines

This is an example rule pack for academic prose diagnostics, adapted from Jan van Gemert's short writing guidelines.

## Rule 1: Do not make the reader wait for the point

Flag prose where the main message arrives only after long setup, especially when a paragraph starts with broad context before stating the actual claim.

Good diagnostics should suggest moving the key point earlier.

## Rule 2: Keep sentences short and direct

Flag sentences that are overloaded with clauses, parentheticals, or multiple ideas.

Good diagnostics should suggest splitting or simplifying the sentence, not merely say that it is long.

## Rule 3: Use concrete subjects and active verbs

Flag vague constructions where the actor is hidden or the sentence relies heavily on nominalizations.

Prefer feedback that asks who does what.

## Rule 4: Put related ideas close together

Flag paragraphs where concepts are introduced far away from their explanations, definitions, examples, or consequences.

Good diagnostics should suggest moving the definition, example, or explanation closer to the first use.

## Rule 5: Avoid unnecessary repetition

Flag repeated claims, terms, or setup that does not add precision or development.

Good diagnostics should identify what is repeated and ask whether the second instance adds anything new.

## Output expectations

When used by the LLM diagnostic path, return only concise diagnostics that can fit in editor virtual text.

Each diagnostic should:

- include a concrete `range_hint`, such as `paragraph 2` or `sentence 1`
- use one of the rule IDs above
- name or quote the specific phrase, claim, actor, or repeated idea that triggered it
- explain the issue in one short sentence
- avoid generic style advice like `Use active voice` without saying where
- avoid rewriting the whole paragraph

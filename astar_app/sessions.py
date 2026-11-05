"""Deterministic session planning. Never rewrites source blocks."""
import math


def session_settings(options):
    mode = options.get('planningMode', 'words')
    if mode not in ('words', 'sessions'):
        raise ValueError('Choose sessions or words planning mode.')
    minutes = int(options.get('sessionMinutes', 30))
    practice = int(options.get('practiceMinutes', 15))
    pace = int(options.get('readingWpm', 120))
    units = int(options.get('expectedUnits', 0) or 0)
    if not 10 <= minutes <= 90 or not 0 <= practice < minutes or not 40 <= pace <= 300 or not 0 <= units <= 2000:
        raise ValueError('Use 10–90 session minutes, practice shorter than the session, 40–300 reading words/minute, and 0–2,000 expected units.')
    return dict(planningMode=mode, sessionMinutes=minutes, practiceMinutes=practice, readingWpm=pace, expectedUnits=units)


def plan_sessions(lessons, settings):
    budget = (settings['sessionMinutes'] - settings['practiceMinutes']) * settings['readingWpm']
    result = []
    current = None
    weight = 0
    for lesson in lessons:
        words = sum(len(b.get('text', '').split()) for b in lesson['blocks'])
        # Image-only material cannot be timed from text: one page per draft session.
        image_only = not words
        if current is None or current['chapterId'] != lesson['chapterId'] or weight + words > budget or image_only or current.get('_imageOnly'):
            current = {**lesson, 'blocks': list(lesson['blocks']), 'panels': list(lesson['panels']), 'questions': list(lesson['questions']), '_imageOnly': image_only}
            result.append(current)
            weight = words
        else:
            current['blocks'].extend(lesson['blocks'])
            current['questions'].extend(lesson['questions'])
            current['panels'] = list({p['page']: p for p in current['panels'] + lesson['panels']}.values())
            current['pageEnd'] = lesson['pageEnd']
            weight += words
    counters = {}
    for n, lesson in enumerate(result, 1):
        chapter = lesson['chapterId']
        counters[chapter] = counters.get(chapter, 0) + 1
        lesson['id'] = f'session-{n}'
        lesson['title'] = f"Session {counters[chapter]} · {lesson['title']}"
        words = sum(len(b.get('text', '').split()) for b in lesson['blocks'])
        lesson['session'] = dict(targetMinutes=settings['sessionMinutes'], readingWords=words,
            estimatedReadingMinutes=math.ceil(words/settings['readingWpm']) if words else None,
            practiceMinutes=settings['practiceMinutes'], timingNeedsReview=True)
        lesson.pop('_imageOnly', None)
    return result

"""Director presentation modes: sparse picture-book vs dense board/infographic.

Not a user option. The model infers a mode from audience and content, writes it on
design.json and storyboard.json, and storyboard_lint enforces the density contract.
"""

MODES = {
    'picture_book': {
        'density': 'sparse',
        'max_hold_seconds': 10,
        'hold_range': (8, 12),
        'cadence_factor': 1.35,
        'max_picture_visuals_per_shot': 1,
        'max_labels_per_shot': 2,
        'board_reuse': False,
        'min_finished_hold_median': 2.0,
        'drawing_share': 0.55,
        'text_role': 'caption_only',
        'summary': '儿童/绘本：单页少内容，大图主导，画完长停',
    },
    'focus_diagram': {
        'density': 'medium',
        'max_hold_seconds': 8,
        'hold_range': (6, 10),
        'cadence_factor': 1.0,
        'max_picture_visuals_per_shot': 2,
        'max_labels_per_shot': 5,
        'board_reuse': False,
        'min_finished_hold_median': 1.2,
        'drawing_share': 0.7,
        'text_role': 'labels',
        'summary': '单概念深挖：一主图+关键标注',
    },
    'dense_infographic': {
        'density': 'dense',
        'max_hold_seconds': 7,
        'hold_range': (5, 9),
        'cadence_factor': 0.9,
        'max_picture_visuals_per_shot': 4,
        'max_labels_per_shot': 12,
        'board_reuse': True,
        'min_finished_hold_median': 0.9,
        'drawing_share': 0.7,
        'text_role': 'module_titles',
        'summary': '知识科普/信息图：单页多模块，结构化密',
    },
    'accumulating_board': {
        'density': 'dense',
        'max_hold_seconds': 12,
        'hold_range': (8, 12),
        'cadence_factor': 0.55,            # same board accumulates; fewer full redraws
        'max_picture_visuals_per_shot': 6,
        'max_labels_per_shot': 16,
        'board_reuse': True,
        'min_finished_hold_median': 0.8,
        'drawing_share': 0.7,
        'text_role': 'board_labels',
        'summary': '黑板报/课堂讲解：底板累积，随讲随写',
    },
    'lecture_annotate': {
        'density': 'dense',
        'max_hold_seconds': 12,
        'hold_range': (8, 12),
        'cadence_factor': 0.55,
        'max_picture_visuals_per_shot': 6,
        'max_labels_per_shot': 16,
        'board_reuse': True,
        'min_finished_hold_median': 0.8,
        'drawing_share': 0.7,
        'text_role': 'board_labels',
        'summary': '课堂笔记/固定讲义页：静态底板铺底，随讲随写笔记标注',
    },
    'step_sequence': {
        'density': 'medium',
        'max_hold_seconds': 8,
        'hold_range': (6, 10),
        'cadence_factor': 1.05,
        'max_picture_visuals_per_shot': 1,
        'max_labels_per_shot': 3,
        'board_reuse': False,
        'min_finished_hold_median': 1.3,
        'drawing_share': 0.6,
        'text_role': 'step_numbers',
        'summary': '步骤教程：一步一焦点，步间清场',
    },
    'narrative_comic': {
        'density': 'medium',
        'max_hold_seconds': 8,
        'hold_range': (6, 10),
        'cadence_factor': 1.1,
        'max_picture_visuals_per_shot': 3,
        'max_labels_per_shot': 4,
        'board_reuse': False,
        'min_finished_hold_median': 1.4,
        'drawing_share': 0.6,
        'text_role': 'balloons_sparse',
        'summary': '叙事漫画：分镜格推进，情绪优先',
    },
}

DEFAULT_MODE = 'focus_diagram'


def get_mode(board_or_design):
    """Read presentation.mode from a storyboard or design document."""
    block = board_or_design.get('presentation') if isinstance(board_or_design, dict) else None
    if not block:
        return None
    mode = block.get('mode')
    if mode not in MODES:
        raise ValueError(f'presentation.mode must be one of {sorted(MODES)}; got {mode!r}')
    if not str(block.get('reason', '')).strip():
        raise ValueError('presentation.reason must explain why this mode fits the audience and content')
    return mode


def policy(mode):
    if mode not in MODES:
        raise ValueError(f'Unknown presentation mode: {mode!r}')
    return dict(MODES[mode])


def validate_presentation(block, where='design.json'):
    if not isinstance(block, dict):
        raise ValueError(f'{where} presentation must be an object')
    mode = block.get('mode')
    if mode not in MODES:
        raise ValueError(f'{where} presentation.mode must be one of {sorted(MODES)}')
    if not str(block.get('reason', '')).strip():
        raise ValueError(f'{where} presentation.reason is required')
    density = block.get('density', MODES[mode]['density'])
    if density != MODES[mode]['density']:
        raise ValueError(f'{where} presentation.density must be {MODES[mode]["density"]!r} for mode {mode}')
    return {'mode': mode, 'density': density, 'reason': block['reason'].strip(),
            'policy': policy(mode), 'summary': MODES[mode]['summary']}


def page_content_policy(mode):
    """Fields the director copies into design.json / per-image briefs."""
    item = policy(mode)
    from composition import MIN_CONTENT_EXTENT
    return {
        'max_heroes_per_page': item['max_picture_visuals_per_shot'],
        'max_labels_per_page': item['max_labels_per_shot'],
        'board_reuse': item['board_reuse'],
        'text_role': item['text_role'],
        'hold_after_draw_s': item['min_finished_hold_median'],
        'stroke_budget_share': item['drawing_share'],
        'content_extent_review_ratio': MIN_CONTENT_EXTENT[mode],
        'composition_required': mode in ('dense_infographic', 'accumulating_board'),
    }


def infer_hints():
    """Soft prior for the model (not enforced as a classifier)."""
    return {
        'picture_book': '受众偏儿童且叙事/绘本为主',
        'focus_diagram': '单概念或单机制深挖',
        'dense_infographic': '对比/清单/结构化知识科普，面向成人或大龄儿童',
        'accumulating_board': '课堂讲解、黑板报、分类列举需连续板书',
        'step_sequence': '操作步骤、流程教程',
        'narrative_comic': '情绪/品牌/故事线，分镜叙事',
    }

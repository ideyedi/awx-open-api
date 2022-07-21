from sqlalchemy.orm import Session

from ..schemas.pipeline import PipelineSchema
from ..models.params import PipelineBuilderParams


def find(db: Session, env: str, key: str, slug: str) -> PipelineSchema:
    """
    env, key, slug 에 일치하는 row 를 찾습니다.

    Args:
        db (Session)
        params (PipelineBuilderParams)

    Returns:
        PipelineSchema: match 된 첫번째 row
    """
    return db.query(PipelineSchema).filter_by(env=env, key=key, slug=slug).first()


def upsert(db: Session, params: PipelineBuilderParams) -> PipelineSchema:
    """
    upsert literally

    Args:
        db (Session)
        params (PipelineBuilderParams)

    Returns:
        PipelineSchema upsert 된 row
    """
    pipeline = find(db, env=params.env, key=params.project, slug=params.name)
    if not pipeline:
        pipeline = PipelineSchema(
            env=params.env,
            key=params.project,
            slug=params.name,
            repository=params.repo,
            raw=params.dict(),
        )
        db.add(pipeline)
    else:
        pipeline.env = params.env
        pipeline.key = params.project
        pipeline.slug = params.name
        pipeline.repository = params.repo
        pipeline.raw = params.dict()

    db.commit()
    db.refresh(pipeline)
    return pipeline

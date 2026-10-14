"""Proposed mathematical components; not fitted, calibrated or labeled WAR."""
from datetime import date
import math


def finite(value):
    if value is None or not math.isfinite(float(value)):
        raise ValueError('Finite observed/estimated input required; missing is not zero')
    return float(value)


def action_probability_change(score_before,score_after,concede_before,concede_after):
    """Same acting-team perspective and horizon required for all four estimates.

    Caller must reconcile possession changes, goals, period boundaries and provider
    events. This arithmetic alone is not a complete VAEP implementation.
    """
    values=list(map(finite,[score_before,score_after,concede_before,concede_after]))
    if any(not 0<=v<=1 for v in values):raise ValueError('Probability outside [0,1]')
    sb,sa,cb,ca=values
    return (sa-sb)-(ca-cb)


def above_baseline(value_per90,baseline_per90,minutes):
    """Inputs must already use the same validated measurement/context scale."""
    player,baseline,minutes=map(finite,[value_per90,baseline_per90,minutes])
    if minutes<0:raise ValueError('Negative exposure')
    return dict(per90=player-baseline,total=(player-baseline)*minutes/90,
                units='same input units, not automatically goals, points or WAR')


def annual_commitment(transfer_fee,contract_years,annual_gross_wages,
                      annual_agent_cost,annual_loan_cost,annual_signing_cost):
    """Accounting scenario, not cash budget; each cost component must be known."""
    fee,years,wage,agent,loan,signing=map(finite,[transfer_fee,contract_years,
        annual_gross_wages,annual_agent_cost,annual_loan_cost,annual_signing_cost])
    if years<=0 or min(fee,wage,agent,loan,signing)<0:raise ValueError('Invalid cost scenario')
    return fee/years+wage+agent+loan+signing


def accessible_baseline(candidates,position,annual_budget,as_of):
    """Weighted expected shortlisted replacement; no oracle best-player choice.

    Membership, compatibility and acceptance weights require reviewed historical
    evidence. Performance reliability must be established before supplying value.
    Missing costs exclude candidates; market value never substitutes for wages.
    """
    budget=finite(annual_budget)
    if budget<0:raise ValueError('Negative annual scenario budget')
    deadline=date.fromisoformat(as_of);accepted=[];excluded=[]
    for candidate in candidates:
        try:
            if not candidate.get('availability_verified') or position not in candidate.get('positions',[]):
                raise ValueError('Availability or role not verified')
            if date.fromisoformat(candidate['information_date'])>deadline:
                raise ValueError('Future information')
            if not candidate.get('performance_reliability_reviewed'):
                raise ValueError('Performance reliability unresolved')
            cost=annual_commitment(**candidate['cost'])
            if cost>budget:raise ValueError('Outside annual scenario budget')
            value=finite(candidate['value_per90']);weight=finite(candidate['acceptance_weight'])
            if weight<=0:raise ValueError('Positive feasibility weight required')
            accepted.append((candidate['id'],value,weight,cost))
        except (ValueError,KeyError,TypeError) as error:
            excluded.append(dict(id=candidate.get('id'),reason=str(error)))
    value=sum(v*w for _,v,w,_ in accepted)/sum(w for _,_,w,_ in accepted) if accepted else None
    return dict(baseline_per90=value,accepted_candidates=accepted,excluded_candidates=excluded,
                status='scenario estimate' if accepted else 'not estimable')


def expected_points(win_probability,draw_probability):
    win,draw=map(finite,[win_probability,draw_probability])
    if min(win,draw)<0 or win+draw>1:raise ValueError('Invalid outcome probabilities')
    return 3*win+draw


def season_specific_total(period_rows,baselines):
    """Subtract each season/stint's own baseline; never reuse a current-year one."""
    result=[]
    for row in period_rows:
        key=(row['season'],row['team'],row['position'],row['comparison'])
        if key not in baselines:
            result.append(dict(key=key,status='missing season-specific baseline',total=None))
            continue
        value=above_baseline(row['value_per90'],baselines[key],row['minutes'])
        result.append(dict(key=key,status='available',**value))
    # Incomplete periods do not become misleadingly complete totals.
    return dict(rows=result,total=sum(r['total'] for r in result) if all(r['total'] is not None for r in result) else None)


  
  # ---
  # title: "INF170 Assignment 2"
  # author: "Martin Andreassen"
  # date: "November 2025"
  # output: pdf_document
  # geometry: margin=1in
  # ---
  
  # ## Q3) Using the PDP model from Question 2 to solve a TSP (no model changes)
  #
  # A Traveling Salesperson Problem (TSP) over a city set $C$ with distance matrix $(d_{uv})_{u,v\in C}$
  # can be solved *without changing the PDP model* by defining the **data** as follows.
  #
  # ### Sets and node construction
  #
  # Let $n = |C|$. Construct:
  #
  # - One **pickup** node $i$ for each city $c_i \in C$: $N_p = \{1, \dots, n\}$
  # - One **delivery** node paired with each pickup: $N_d = \{n+1, \dots, 2n\}$,
  #   where $n+i$ is the delivery for pickup $i$
  # - Two dummy depots: origin $o$ and destination $d$
  # - Full node set: $N_v = \{o, d\} \cup N_p \cup N_d$
  # - Arc set: $A = \{(u,v) \in N_v \times N_v : u \neq v\}$
  #
  # ### Distances
  #
  # Make each pickup–delivery pair co-located so visiting a city happens as *pickup then immediate delivery*:
  #
  # $$ D_{i,n+i} = D_{n+i,i} = 0 \quad \forall i \in N_p. $$
  #
  # For moves between different cities, copy TSP distances:
  #
  # $$
  # \begin{aligned}
  # D_{i,j} &= d_{c_i,c_j}, \\
  # D_{i,n+j} &= d_{c_i,c_j}, \\
  # D_{n+i,j} &= d_{c_i,c_j}, \\
  # D_{n+i,n+j} &= d_{c_i,c_j},
  # \qquad \text{for all } i \neq j.
  # \end{aligned}
  # $$
  #
  # For the depots, set distances to match the chosen start/end convention
  # (e.g., co-locate both with a depot):
  #
  # $$ D_{o,i} = d_{\text{depot},c_i}, \qquad D_{n+i,d} = d_{c_i,\text{depot}}. $$
  #
  # If you want a pure cycle, identify $d$ with $o$ in interpretation.
  #
  # ### Loads and capacity
  #
  # Choose small non-negative loads to keep capacity non-binding, e.g.
  #
  # $$ Q_i = 1 \quad \forall i \in N_p, \qquad K \ge \sum_{i \in N_p} Q_i. $$
  #
  # This keeps constraints (6)–(8) valid but non-restrictive.
  #
  # ### Spot-charter variable
  #
  # Forbid outsourcing by setting a prohibitive spot cost:
  #
  # $$ C_S \text{ very large (e.g., } 999{,}999\text{),} $$
  #
  # so constraint (2) forces $y_i = 0$ and each city must be visited by the vehicle.
  #
  # ### Time linking and precedence
  #
  # Keep the time constraints (9)–(12) with a valid big-M
  # (e.g., $M = \max_{u,v} D_{uv} \cdot |N_v|$)
  # to enforce a consistent ordering and pickup-before-delivery.
  # Because $D_{i,n+i} = 0$, the optimal solution visits $(i, n+i)$ back-to-back,
  # meaning each city is effectively visited once.
  #
  # ### Recovering the TSP tour
  #
  # Ignore $o$ and $d$ and collapse each pair $(i, n+i)$ into a single city $i$.
  # The sequence of pickups (or of pickup–delivery pairs) yields the TSP tour order.
  # The objective equals the TSP tour length since city-to-city movements use $d_{c_i,c_j}$
  # and intra-pair moves have cost 0.
  #
  # ### Consistency with our run
  #
  # In our experiment we used $|N_v| = 22$, $|N_p| = 10$, $|N_d| = 10$, $o = 21$, $d = 22$,
  # $K = 10{,}000$ (non-binding), $C_S = 999{,}999$ (forbids $y_i = 1$),
  # and $M = 25$ with a dense $D$.
  # The solver returned an **optimal** solution (gap = 0.0000 %), which corresponds to
  # the TSP optimum induced by $D$ under this PDP encoding.
    




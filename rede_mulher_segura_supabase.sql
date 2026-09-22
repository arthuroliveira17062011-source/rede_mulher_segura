-- ============================================================
-- REDE MULHER SEGURA — Banco de Dados
-- Versão: SUPABASE (PostgreSQL)
-- ============================================================

-- Extensão usada para gerar UUIDs (recomendado no Supabase,
-- já que a autenticação nativa do Supabase usa UUID em auth.users)
create extension if not exists "pgcrypto";

-- ------------------------------------------------------------
-- 1. USUARIA
-- ------------------------------------------------------------
create table public.usuaria (
    id_usuario           uuid primary key default gen_random_uuid(),
    nome_completo         text not null,
    cpf                   text not null unique,
    email                 text not null unique,
    telefone_celular      text not null unique,
    data_nascimento       date not null,
    endereco_residencia   text,
    senha_hash            text not null,
    frase_chave           text,
    criado_em             timestamptz not null default now()
);

comment on table public.usuaria is 'Dados cadastrais da usuária do aplicativo';
comment on column public.usuaria.senha_hash is 'Senha criptografada usada para acessar a área segura de provas';
comment on column public.usuaria.frase_chave is 'Frase-comando usada para ativar o alerta por voz';

-- ------------------------------------------------------------
-- 2. CONTATO_EMERGENCIA
-- ------------------------------------------------------------
create table public.contato_emergencia (
    id_contato             uuid primary key default gen_random_uuid(),
    id_usuario             uuid not null references public.usuaria (id_usuario) on delete cascade,
    nome_completo           text not null,
    telefone_whatsapp       text not null,
    prioridade_notificacao  integer not null,
    criado_em               timestamptz not null default now()
);

comment on table public.contato_emergencia is 'Contatos de confiança que recebem o alerta de socorro';
comment on column public.contato_emergencia.prioridade_notificacao is 'Ordem em que o contato é avisado (1 = primeiro a ser notificado)';

-- ------------------------------------------------------------
-- 3. OCORRENCIAS_DE_ALERTA
-- ------------------------------------------------------------
create table public.ocorrencias_de_alerta (
    id_alerta                      uuid primary key default gen_random_uuid(),
    id_usuario                     uuid not null references public.usuaria (id_usuario) on delete cascade,
    data_hora_ativacao             timestamptz not null default now(),
    tipo_ativacao                  text not null check (tipo_ativacao in ('botao', 'comando_voz', 'temporizador')),
    link_google_maps_localizacao   text,
    link_compartilhamento          text
);

comment on table public.ocorrencias_de_alerta is 'Registro de cada vez que o alerta de socorro foi ativado';
comment on column public.ocorrencias_de_alerta.tipo_ativacao is 'Como o alerta foi disparado: botão, comando de voz ou temporizador sem cancelamento';
comment on column public.ocorrencias_de_alerta.link_google_maps_localizacao is 'Link com a localização exata registrada no momento do alerta';
comment on column public.ocorrencias_de_alerta.link_compartilhamento is 'Link gerado para compartilhamento do alerta (ex: com a polícia ou contatos)';

-- ------------------------------------------------------------
-- 4. MIDIA_PROVAS
-- ------------------------------------------------------------
create table public.midia_provas (
    id_midia                 uuid primary key default gen_random_uuid(),
    id_alerta                uuid not null references public.ocorrencias_de_alerta (id_alerta) on delete cascade,
    id_usuario                uuid not null references public.usuaria (id_usuario) on delete cascade,
    tipo_arquivo              text not null check (tipo_arquivo in ('audio', 'video', 'imagem')),
    caminho_arquivo_nuvem     text not null,
    tamanho_arquivo_bytes     bigint not null,
    data_hora_registro        timestamptz not null default now()
);

comment on table public.midia_provas is 'Arquivos de áudio/vídeo/imagem coletados automaticamente como prova durante o alerta';
comment on column public.midia_provas.caminho_arquivo_nuvem is 'Caminho do arquivo no Supabase Storage (bucket privado)';

-- ------------------------------------------------------------
-- 5. CONFIGURACOES_DE_SEGURANCA
-- ------------------------------------------------------------
create table public.configuracoes_de_seguranca (
    id_configuracao              uuid primary key default gen_random_uuid(),
    id_usuario                   uuid not null unique references public.usuaria (id_usuario) on delete cascade,
    tempo_temporizador_segundo   integer,
    pin_desativado               text,
    tema_disfarce_padrao         text default 'cardapio_restaurante'
);

comment on table public.configuracoes_de_seguranca is 'Preferências de segurança e disfarce definidas pela usuária';
comment on column public.configuracoes_de_seguranca.tempo_temporizador_segundo is 'Tempo (em segundos) até o envio automático do alerta caso não seja cancelado';
comment on column public.configuracoes_de_seguranca.pin_desativado is 'PIN usado para cancelar um alerta disparado por engano';
comment on column public.configuracoes_de_seguranca.tema_disfarce_padrao is 'Tela de disfarce exibida por padrão (ex: cardápio de restaurante)';

-- ------------------------------------------------------------
-- ÍNDICES ÚTEIS
-- ------------------------------------------------------------
create index idx_contato_emergencia_usuario on public.contato_emergencia (id_usuario);
create index idx_ocorrencias_usuario on public.ocorrencias_de_alerta (id_usuario);
create index idx_midia_alerta on public.midia_provas (id_alerta);
create index idx_midia_usuario on public.midia_provas (id_usuario);

-- ------------------------------------------------------------
-- ROW LEVEL SECURITY (RECOMENDADO PARA ESTE TIPO DE APP)
-- ------------------------------------------------------------
-- Como os dados são sensíveis (localização, contatos, provas),
-- é essencial que cada usuária só enxergue os próprios dados.
-- Isso pressupõe login via Supabase Auth, onde auth.uid() = id_usuario.

alter table public.usuaria enable row level security;
alter table public.contato_emergencia enable row level security;
alter table public.ocorrencias_de_alerta enable row level security;
alter table public.midia_provas enable row level security;
alter table public.configuracoes_de_seguranca enable row level security;

create policy "usuaria_ve_apenas_seus_dados"
    on public.usuaria for select
    using (auth.uid() = id_usuario);

create policy "usuaria_atualiza_apenas_seus_dados"
    on public.usuaria for update
    using (auth.uid() = id_usuario);

create policy "contato_emergencia_por_usuaria"
    on public.contato_emergencia for all
    using (auth.uid() = id_usuario);

create policy "ocorrencias_por_usuaria"
    on public.ocorrencias_de_alerta for all
    using (auth.uid() = id_usuario);

create policy "midia_provas_por_usuaria"
    on public.midia_provas for all
    using (auth.uid() = id_usuario);

create policy "configuracoes_por_usuaria"
    on public.configuracoes_de_seguranca for all
    using (auth.uid() = id_usuario);

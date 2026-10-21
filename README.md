# Busca Geoespacial --- Belo Horizonte

Aplicação acadêmica de busca geoespacial de estabelecimentos em Belo
Horizonte, com indexação por **Geohash + Trie**, busca por raio e
simulação de entregadores posicionados na malha viária do OpenStreetMap.

## Funcionalidades

-   Carregamento e normalização dos estabelecimentos a partir de
    `data/bares.csv`.
-   Associação dos estabelecimentos aos bairros disponíveis no arquivo
    geográfico da PBH.
-   Uso de um ponto representativo do polígono de cada bairro como
    coordenada aproximada dos estabelecimentos associados a ele.
-   Codificação das coordenadas em Geohash, com precisão configurável de
    até 8 caracteres.
-   Indexação dos Geohashes em uma Trie.
-   Busca de estabelecimentos por nome, endereço ou bairro.
-   Busca espacial por raio, limitada a 2.000 metros, com filtragem
    final por distância de Haversine.
-   Mapa interativo com o estabelecimento selecionado, círculo do raio e
    estabelecimentos encontrados.
-   Geração de entregadores sintéticos e ajuste de suas posições à
    aresta viária mais próxima disponível no grafo do OpenStreetMap.
-   Classificação dinâmica dos entregadores: **verde** quando dentro do
    raio escolhido e **cinza** quando fora dele.
-   Estimativa ilustrativa de ETA com velocidade constante de 20 km/h.

## Tecnologias

-   Python
-   Streamlit
-   Folium e streamlit-folium
-   Pandas
-   Geohash implementado no projeto
-   Trie implementada no projeto
-   Shapely e PyProj para operações geométricas e transformação de
    coordenadas
-   OSMnx para obter e consultar o grafo viário do OpenStreetMap

As dependências Python estão listadas em `requirements.txt`.

## Requisitos

-   Windows, macOS ou Linux com Python compatível com as dependências do
    `requirements.txt`.
-   Conexão com a internet na primeira geração de entregadores para
    baixar o grafo viário do OpenStreetMap.
-   Arquivos de dados presentes nos caminhos descritos abaixo.

## Execução

Na raiz do projeto, com o ambiente virtual ativado, execute:

``` powershell
python -m streamlit run app.py
```

O Streamlit informará o endereço local da aplicação no terminal e
normalmente abrirá o navegador automaticamente. Para encerrar a
aplicação, volte ao terminal e pressione `Ctrl + C`.

## Como usar

1.  Aguarde o carregamento do índice geoespacial.
2.  Digite parte do nome, endereço ou bairro no campo de busca.
3.  Selecione um estabelecimento na lista.
4.  Ajuste o raio de busca entre 100 m e 2.000 m.
5.  Consulte os estabelecimentos encontrados e suas distâncias
    aproximadas.
6.  Informe a quantidade de entregadores sintéticos e clique em **Gerar
    / substituir entregadores**.
7.  Na primeira geração para uma região, aguarde o download e o
    processamento do grafo viário do OpenStreetMap. O grafo é salvo em
    cache local para reutilização.
8.  Altere o raio sem gerar novamente os entregadores para observar a
    atualização de disponibilidade: verde significa dentro do raio;
    cinza significa fora dele.


### Teste manual da interface

-   Pesquisar por nome e por bairro.
-   Selecionar um estabelecimento e conferir o círculo do raio.
-   Gerar entregadores e verificar se os pinos estão sobre vias
    representadas no grafo.
-   Reduzir e aumentar o raio sem gerar novamente os entregadores; os
    status e as cores devem mudar de acordo com a distância.
-   Trocar o estabelecimento de referência e confirmar que a aplicação
    solicita uma nova geração para a nova referência.
-   Testar uma região sem conexão ou com falha de acesso ao
    OpenStreetMap e verificar se a aplicação informa o erro.

## Dados, aproximações e limitações

**Coordenadas dos estabelecimentos.** A base CSV não fornece coordenadas
geográficas exatas para cada endereço. Para permitir a busca espacial,
cada estabelecimento é associado ao ponto representativo do polígono de
seu bairro. Consequentemente, estabelecimentos do mesmo bairro podem
compartilhar coordenadas e as distâncias calculadas são aproximadas; não
devem ser interpretadas como distâncias reais entre endereços.

**Entregadores.** Os pontos são inicialmente gerados aleatoriamente em
torno da referência e depois projetados sobre a geometria da aresta
viária mais próxima no grafo de condução obtido pelo OSMnx. O resultado
depende da cobertura e da classificação da malha viária do
OpenStreetMap; isso não garante condições reais de acesso ou circulação.

**ETA.** O tempo é uma estimativa demonstrativa calculada com velocidade
constante de 20 km/h e distância em linha reta. Não é uma rota nem um
tempo de percurso rodoviário.

**Internet e cache.** A primeira consulta do grafo depende de conexão
com a internet e dos serviços do OpenStreetMap. O grafo é armazenado em
`data/osmnx_graphs/`; esse cache é um artefato gerado localmente e não
precisa ser versionado.

**Atribuição de dados.** O arquivo geográfico de bairros foi obtido no
portal CKAN da Prefeitura de Belo Horizonte: [Bairro Popular --- recurso
geográfico](https://ckan.pbh.gov.br/dataset/bairro-popular/resource/710e73a6-c0b8-41e5-ad08-b6b9e33564dd).
Os dados viários são provenientes do
[OpenStreetMap](https://www.openstreetmap.org/) e estão sujeitos aos
termos e à atribuição da OpenStreetMap Foundation.


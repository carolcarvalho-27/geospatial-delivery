# Relatório Técnico --- Indexação Geoespacial e Geometria Computacional Híbrida

## 1. Objetivo

O projeto implementa uma aplicação de busca geoespacial de
estabelecimentos em Belo Horizonte. A solução combina uma estrutura de
indexação própria, busca por proximidade, visualização cartográfica e
geração de entregadores sintéticos ajustados à malha viária disponível
no OpenStreetMap.

O objetivo não é apenas demonstrar uma interface de mapa: o núcleo do
trabalho implementa Geohash, uma Trie e uma etapa de filtragem
geométrica exata por distância, reduzindo a necessidade de comparar a
consulta com todos os registros da base.

## 2. Organização da solução

A implementação foi separada em módulos com responsabilidades
específicas:

-   `geohash.py`: codificação de latitude e longitude em uma string
    Geohash Base32.
-   `trie.py`: estrutura de prefixos usada para indexar e recuperar
    registros por Geohash.
-   `geo_distance.py`: cálculo de distância geográfica pela fórmula de
    Haversine.
-   `spatial_index.py`: integração entre Geohash, Trie, geração de
    prefixos candidatos, filtragem por raio e ordenação dos resultados.
-   `establishments.py`: leitura e normalização dos registros CSV e
    montagem de endereços textuais.
-   `neighborhoods.py`: leitura das geometrias dos bairros,
    transformação de coordenadas e obtenção de pontos representativos.
-   `approximate_index_builder.py`: associação dos estabelecimentos aos
    bairros e construção do índice aproximado.
-   `app.py`: interface Streamlit, mapa Folium, geração de entregadores,
    cálculo de disponibilidade e interação com o OSMnx.

Essa divisão facilita testes unitários e permite alterar a interface sem
reimplementar a estrutura de dados.

## 3. Preparação e qualidade dos dados

A base `data/bares.csv` contém os dados tabulares dos estabelecimentos,
mas não possui coordenadas exatas de latitude e longitude para cada
endereço. Para possibilitar a indexação espacial, os registros são
associados a polígonos de bairros fornecidos em arquivo geográfico.

As geometrias dos bairros são transformadas do sistema de coordenadas
projetado para latitude e longitude. Em seguida, é calculado um ponto
representativo de cada polígono, usado como coordenada aproximada para
os estabelecimentos daquele bairro.

A correspondência entre os nomes dos bairros é normalizada, incluindo
diferenças de acentuação, caixa alta e espaços. Também há variações de nomes
para nomes equivalentes conhecidos. As variações dos nomes são decisões de normalização
e foram feitas para os dados fornecidos; uma correspondência
nominal não confirmada pode associar um registro ao bairro incorreto.

Na execução de validação mais recente registrada durante o
desenvolvimento, a base tinha 20.859 estabelecimentos, dos quais 20.696
foram indexados e 163 ficaram sem correspondência. Esses números são uma
fotografia da versão dos dados e das regras de correspondência usadas
naquela execução; devem ser recalculados caso a base ou os nomes sejam
alterados.

### Consequência da aproximação

A coordenada representativa pertence ao bairro, mas não representa
necessariamente o endereço comercial real. Assim, vários
estabelecimentos do mesmo bairro podem receber a mesma coordenada. Isso
pode produzir distâncias zero entre estabelecimentos diferentes e
distâncias pouco representativas da realidade. A limitação é apresentada
na interface e deve ser considerada na interpretação dos resultados.

## 4. Geohash e Trie

### 4.1 Codificação Geohash

O módulo `geohash.py` divide recursivamente os intervalos de latitude e
longitude e intercala os bits de cada coordenada. Os grupos de cinco
bits são convertidos em caracteres do alfabeto Base32 usado pelo
Geohash.

A precisão utilizada na construção do índice é de até oito caracteres. A
string codificada representa uma célula geográfica: quanto maior a
precisão, menor tende a ser a célula.

**Complexidade:** para uma precisão `p`, a codificação custa `O(p)`
tempo. Como o projeto limita `p` a, no máximo, oito caracteres, o custo
é constante para os parâmetros permitidos (`O(1)` sob esse limite fixo).

### 4.2 Trie

A Trie armazena os Geohashes como caminhos de caracteres, compartilhando
prefixos entre chaves. Isso permite localizar a subárvore associada a um
prefixo sem percorrer todas as chaves completas desde o início.

Para uma chave de comprimento `p`, a inserção ou a localização do nó
correspondente ao prefixo custa `O(p)`. A recuperação dos registros de
uma subárvore também depende do tamanho dessa subárvore e da quantidade
de registros retornados. Em termos precisos, o custo da consulta por
prefixo é `O(p + s + k)`, em que `s` é o número de nós visitados na
subárvore e `k` é o número de registros retornados. Em uma análise
simplificada em que a enumeração é proporcional à saída, costuma-se
expressar o custo como `O(p + k)`.

O dicionário interno de registros por identificador também permite
substituir um registro existente sem manter uma cópia antiga no índice.

## 5. Busca por raio

A busca espacial é realizada em duas fases:

1.  **Geração de candidatos:** o sistema calcula a região geográfica que
    cobre o raio solicitado e gera prefixos Geohash para as células que
    intersectam essa região. A precisão de busca pode ser reduzida para
    evitar a geração de uma quantidade excessiva de células candidatas.
2.  **Filtragem exata:** os registros candidatos são analisados (cópias removidas) por
    identificador e sua distância até o ponto de consulta é calculada
    pela fórmula de Haversine. Apenas registros com distância menor ou
    igual ao raio são mantidos. Os resultados são ordenados pela
    distância crescente.

A primeira fase favorece a eficiência, mas pode incluir falsos
positivos, pois as células Geohash não coincidem exatamente com o
círculo. A segunda fase remove esses candidatos externos ao raio.

Se `c` é o número de células candidatas, `q` é o número de registros
candidatos após a recuperação pela Trie e `r` é o número de resultados
finais, a filtragem de distâncias custa `O(q)` e a ordenação custa
`O(r log r)`. O custo total pode ser descrito como:

`O(c + custo da recuperação dos prefixos + q + r log r)`.

Esse custo depende da distribuição espacial dos dados e da quantidade de
candidatos. No pior caso, uma consulta que cubra uma região com grande
parte dos registros pode examinar uma fração grande do índice. A
estratégia reduz o trabalho em consultas locais, mas não elimina o pior
caso linear.

A fórmula de Haversine usa um número constante de operações aritméticas
e trigonométricas, portanto seu custo assintótico por par de coordenadas
é `O(1)`.

## 6. Geração e ajuste viário dos entregadores

O aplicativo gera uma quantidade configurável de pontos sintéticos em
torno do estabelecimento selecionado. A distância radial inicial usa
`raio × sqrt(U)`, com `U` uniforme entre zero e um, para distribuir
pontos pela área do círculo em vez de concentrá-los no centro. Um ângulo
aleatório determina a direção.

Como pontos puramente aleatórios podem cair dentro de edifícios,
quarteirões fechados ou lagos/lagoas, o sistema usa OSMnx para obter um
grafo de vias de condução em torno do ponto de referência. O grafo é
armazenado localmente em formato GraphML e reutilizado quando
disponível. Ele é projetado para um sistema de coordenadas métrico antes
da busca geométrica.

Para cada coordenada sintética, o OSMnx localiza a aresta viária mais
próxima. Com Shapely, o ponto é projetado sobre a geometria dessa
aresta; a coordenada corrigida é transformada novamente para latitude e
longitude. Usar a geometria da aresta, em vez de simplesmente escolher o
nó mais próximo, permite posicionar o pino ao longo da rua.

Se `n` é o número de entregadores e `E` é o número de arestas do grafo,
a geração inicial é `O(n)`. A busca de arestas usa os mecanismos
espaciais do OSMnx; seu desempenho prático depende do índice espacial e
da complexidade geométrica das vias, por isso não é adequado prometer um
limite assintótico estrito independente da implementação da biblioteca.
O processamento de cada ponto também envolve a projeção sobre a
geometria da aresta selecionada.

O grafo é obtido para uma região limitada ao redor da referência, com
margem em relação ao raio máximo de busca. Isso controla o volume de
dados baixados, mas significa que a solução depende da cobertura da
malha dentro desse recorte.

## 7. Disponibilidade e estimativa de ETA

A disponibilidade dos entregadores é recalculada a cada atualização da
interface. A distância é medida entre a coordenada selecionada e a
posição já corrigida do entregador:

-   verde: distância menor ou igual ao raio atual;
-   cinza: distância maior que o raio atual.

Mudar o raio não gera novos entregadores nem altera suas coordenadas. A
distância e o status são calculados a partir da mesma medição para
manter a consistência entre o mapa e a tabela.

O ETA é uma estimativa demonstrativa baseada em velocidade constante de
20 km/h e distância em linha reta. Não considera a geometria completa de
uma rota, sentidos de circulação, congestionamento ou tempo de espera.
Um ETA realista exigiria calcular rotas na rede viária e estimar custos
de deslocamento.

## 8. Complexidade resumida

  -----------------------------------------------------------------------
  Operação                            Complexidade / observação
  ----------------------------------- -----------------------------------
  Codificar Geohash                   `O(p)`, em que `p` é a precisão;
                                      constante com `p ≤ 8`.

  Inserir registro na Trie            `O(p)` para percorrer/criar o
                                      caminho, além do custo associado ao
                                      registro.

  Localizar prefixo na Trie           `O(p)` para alcançar o prefixo.

  Enumerar registros de um prefixo    `O(s + k)`, em que `s` é o número
                                      de nós visitados e `k` a quantidade
                                      de registros retornados.

  Construir índice de `N` registros   `O(Np)` para as inserções, além da
                                      leitura e normalização; `O(N)`
                                      quando `p` é limitado.

  Calcular distância Haversine        `O(1)` por par de coordenadas.

  Filtrar `q` candidatos por          `O(q)`.
  distância                           

  Ordenar `r` resultados              `O(r log r)`.

  Gerar `n` pontos sintéticos         `O(n)` antes do ajuste viário.

  Ajustar pontos às vias              Depende do índice espacial e das
                                      geometrias do grafo usado pelo
                                      OSMnx/Shapely; não se atribui um
                                      limite estrito independente dessas
                                      bibliotecas.

  Pesquisa textual na interface       `O(N)` por atualização, pois
                                      percorre os registros carregados
                                      para comparar nome, endereço e
                                      bairro.
  -----------------------------------------------------------------------

O espaço de memória do índice é `O(Np)` no limite superior, além dos
dados dos registros e das estruturas de nós da Trie. Com `p` limitado,
isso é linear em relação ao número de estabelecimentos. O grafo viário
ocupa memória adicional proporcional ao número de nós, arestas e
geometrias do recorte carregado.

## 9. Testes e validação

Durante o desenvolvimento foram executados testes automatizados dos
módulos de Geohash, Trie, cálculo de distância, índice espacial,
carregamento dos estabelecimentos e associação aos bairros. A suíte deve
ser executada novamente após qualquer alteração final:

``` powershell
python -m unittest discover -s tests -v
```

Também estão disponíveis scripts de validação do índice e da associação
aproximada aos bairros, conforme os arquivos presentes na pasta
`scripts/`.

A interface foi validada manualmente para pesquisa textual, seleção de
referência, ajuste do raio, geração/substituição dos entregadores, cores
de disponibilidade e visualização dos pontos corrigidos sobre a malha
viária.

## 10. Limitações e melhorias futuras

1.  **Geocodificação dos endereços:** substituir o ponto representativo
    do bairro por coordenadas reais e verificadas de cada
    estabelecimento.
2.  **Correspondência de bairros:** revisar nomes e registros sem
    correspondência, sem assumir equivalência apenas por semelhança
    textual.
3.  **Roteamento real:** calcular distância de percurso e ETA pela rede
    viária, em vez de usar distância em linha reta.
4.  **Acessibilidade viária:** o grafo `drive` representa vias de
    condução conforme o OpenStreetMap; não garante condições em tempo
    real nem acesso a todos os tipos de veículo.
5.  **Desempenho:** medir tempos de construção do índice, quantidade de
    candidatos por consulta e tempos de busca para diferentes raios e
    conjuntos de dados.


## 11. Fontes e atribuição

-   Dados geográficos dos bairros: [Prefeitura de Belo Horizonte ---
    Bairro Popular, recurso
    CKAN](https://ckan.pbh.gov.br/dataset/bairro-popular/resource/710e73a6-c0b8-41e5-ad08-b6b9e33564dd).
-   Dados de vias: [OpenStreetMap](https://www.openstreetmap.org/),
    sujeito aos termos e requisitos de atribuição da OpenStreetMap
    Foundation.
-   Biblioteca para obtenção e consulta do grafo viário: [documentação
    do OSMnx](https://osmnx.readthedocs.io/).
